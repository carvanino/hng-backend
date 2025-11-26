import { Injectable, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as nodemailer from 'nodemailer';
import { Transporter } from 'nodemailer';
import { PrismaService } from '../prisma/prisma.service';
import { TemplatesService } from '../templates/templates.service';
import * as amqp from 'amqp-connection-manager';
import { ChannelWrapper } from 'amqp-connection-manager';
import { ConfirmChannel, ConsumeMessage } from 'amqplib';
import { RabbitMQConfig } from '../config/rabbitmq.config';

interface EmailMessage {
  notification_id: string;
  user_id: string;
  type: string;
  template_id?: string;
  recipient: string;
  subject?: string;
  content: string;
  metadata?: Record<string, any>;
  created_at: Date;
}

@Injectable()
export class EmailService implements OnModuleInit {
  private transporter: Transporter;
  private connection: amqp.AmqpConnectionManager;
  private channelWrapper: ChannelWrapper;

  constructor(
    private configService: ConfigService,
    private prisma: PrismaService,
    private templatesService: TemplatesService,
  ) {
    console.log("SMTP HOST ->", this.configService.get<string>('SMTP_HOST'))
    this.transporter = nodemailer.createTransport({
      host: this.configService.get<string>('SMTP_HOST'),
      port: this.configService.get<number>('SMTP_PORT'),
      secure: this.configService.get<boolean>('SMTP_SECURE'),
      auth: {
        user: this.configService.get<string>('SMTP_USER'),
        pass: this.configService.get<string>('SMTP_PASSWORD'),
      },
    });
  }

  async onModuleInit() {
    await this.startConsumer();
  }

  private async startConsumer() {
    this.connection = amqp.connect([RabbitMQConfig.url]);

    this.channelWrapper = this.connection.createChannel({
      setup: async (channel: ConfirmChannel) => {
        await channel.assertQueue(RabbitMQConfig.queues.email, { durable: true });
        await channel.prefetch(1); // Process one message at a time

        await channel.consume(
          RabbitMQConfig.queues.email,
          async (msg: ConsumeMessage | null) => {
            if (msg) {
              await this.handleMessage(msg, channel);
            }
          },
          { noAck: false }
        );

        console.log('Email service started, waiting for messages...');
      },
    });

    await this.channelWrapper.waitForConnect();
  }

  private async handleMessage(msg: ConsumeMessage, channel: ConfirmChannel) {
    try {
      const message: EmailMessage = JSON.parse(msg.content.toString());
      console.log(`Processing email notification: ${message.notification_id}`);

      await this.processEmail(message);

      // Acknowledge message
      channel.ack(msg);
      console.log(`Email sent successfully: ${message.notification_id}`);
    } catch (error) {
      console.error('Error processing email:', error);

      // Retry logic with exponential backoff
      const retryCount = (msg.properties.headers['x-retry-count'] || 0) + 1;
      const maxRetries = 3;

      if (retryCount <= maxRetries) {
        // Retry with delay
        const delay = Math.pow(2, retryCount) * 1000; // Exponential backoff

        setTimeout(async () => {
          await channel.sendToQueue(
            RabbitMQConfig.queues.email,
            msg.content,
            {
              headers: { 'x-retry-count': retryCount },
              persistent: true,
            }
          );
          channel.ack(msg);
        }, delay);

        console.log(`Retrying email (attempt ${retryCount}/${maxRetries}): ${JSON.parse(msg.content.toString()).notification_id}`);
      } else {
        // Max retries exceeded, move to dead letter queue
        await channel.sendToQueue(
          RabbitMQConfig.queues.failed,
          msg.content,
          { persistent: true }
        );
        channel.ack(msg);

        // Update notification status
        const message: EmailMessage = JSON.parse(msg.content.toString());
        await this.prisma.notification.update({
          where: { id: message.notification_id },
          data: {
            status: 'failed',
            error_message: error.message || 'Failed after max retries',
          },
        });

        console.log(`Email moved to failed queue after ${maxRetries} retries: ${message.notification_id}`);
      }
    }
  }

  private async processEmail(message: EmailMessage) {
    let subject = message.subject;
    let body = message.content;

    // If template_id is provided, render the template
    if (message.template_id && message.metadata) {
      const rendered = await this.templatesService.renderTemplate(
        message.template_id,
        message.metadata
      );
      subject = rendered.subject || subject;
      body = rendered.body;
    }

    // Send email
    await this.transporter.sendMail({
      from: this.configService.get<string>('SMTP_FROM'),
      to: message.recipient,
      subject: subject,
      html: body,
    });

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