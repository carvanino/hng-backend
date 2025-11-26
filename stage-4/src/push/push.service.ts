import { Injectable, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as admin from 'firebase-admin';
import { PrismaService } from '../prisma/prisma.service';
import { TemplatesService } from '../templates/templates.service';
import * as amqp from 'amqp-connection-manager';
import { ChannelWrapper } from 'amqp-connection-manager';
import { ConfirmChannel, ConsumeMessage } from 'amqplib';
import { RabbitMQConfig } from '../config/rabbitmq.config';

interface PushMessage {
  notification_id: string;
  user_id: string;
  type: string;
  template_id?: string;
  recipient: string; // FCM token
  subject?: string;
  content: string;
  metadata?: Record<string, any>;
  created_at: Date;
}

@Injectable()
export class PushService implements OnModuleInit {
  private connection: amqp.AmqpConnectionManager;
  private channelWrapper: ChannelWrapper;

  constructor(
    private configService: ConfigService,
    private prisma: PrismaService,
    private templatesService: TemplatesService,
  ) {
    // Initialize Firebase Admin
    if (!admin.apps.length) {
      admin.initializeApp({
        credential: admin.credential.cert({
          projectId: this.configService.get<string>('FIREBASE_PROJECT_ID'),
          privateKey: this.configService.get<string>('FIREBASE_PRIVATE_KEY')?.replace(/\\n/g, '\n'),
          clientEmail: this.configService.get<string>('FIREBASE_CLIENT_EMAIL'),
        }),
      });
    }
  }

  async onModuleInit() {
    await this.startConsumer();
  }

  private async startConsumer() {
    this.connection = amqp.connect([RabbitMQConfig.url]);

    this.channelWrapper = this.connection.createChannel({
      setup: async (channel: ConfirmChannel) => {
        await channel.assertQueue(RabbitMQConfig.queues.push, { durable: true });
        await channel.prefetch(1);

        await channel.consume(
          RabbitMQConfig.queues.push,
          async (msg: ConsumeMessage | null) => {
            if (msg) {
              await this.handleMessage(msg, channel);
            }
          },
          { noAck: false }
        );

        console.log('Push service started, waiting for messages...');
      },
    });

    await this.channelWrapper.waitForConnect();
  }

  private async handleMessage(msg: ConsumeMessage, channel: ConfirmChannel) {
    try {
      const message: PushMessage = JSON.parse(msg.content.toString());
      console.log(`Processing push notification: ${message.notification_id}`);

      await this.processPush(message);

      channel.ack(msg);
      console.log(`Push notification sent successfully: ${message.notification_id}`);
    } catch (error) {
      console.error('Error processing push notification:', error);

      const retryCount = (msg.properties.headers['x-retry-count'] || 0) + 1;
      const maxRetries = 3;

      if (retryCount <= maxRetries) {
        const delay = Math.pow(2, retryCount) * 1000;

        setTimeout(async () => {
          await channel.sendToQueue(
            RabbitMQConfig.queues.push,
            msg.content,
            {
              headers: { 'x-retry-count': retryCount },
              persistent: true,
            }
          );
          channel.ack(msg);
        }, delay);

        console.log(`Retrying push (attempt ${retryCount}/${maxRetries}): ${JSON.parse(msg.content.toString()).notification_id}`);
      } else {
        await channel.sendToQueue(
          RabbitMQConfig.queues.failed,
          msg.content,
          { persistent: true }
        );
        channel.ack(msg);

        const message: PushMessage = JSON.parse(msg.content.toString());
        await this.prisma.notification.update({
          where: { id: message.notification_id },
          data: {
            status: 'failed',
            error_message: error.message || 'Failed after max retries',
          },
        });

        console.log(`Push moved to failed queue after ${maxRetries} retries: ${message.notification_id}`);
      }
    }
  }

  private async processPush(message: PushMessage) {
    let title = message.subject || 'Notification';
    let body = message.content;

    // If template_id is provided, render the template
    if (message.template_id && message.metadata) {
      const rendered = await this.templatesService.renderTemplate(
        message.template_id,
        message.metadata
      );
      title = rendered.subject || title;
      body = rendered.body;
    }

    // Validate FCM token format
    if (!message.recipient || message.recipient.length < 10) {
      throw new Error('Invalid FCM token');
    }

    // Send push notification via FCM
    const fcmMessage = {
      token: message.recipient,
      notification: {
        title: title,
        body: body,
      },
      data: message.metadata || {},
    };

    await admin.messaging().send(fcmMessage);

    // Update notification status
    await this.prisma.notification.update({
      where: { id: message.notification_id },
      data: {
        status: 'sent',
        sent_at: new Date(),
      },
    });
  }

  async onModuleDestroy() {
    await this.channelWrapper.close();
    await this.connection.close();
  }
}