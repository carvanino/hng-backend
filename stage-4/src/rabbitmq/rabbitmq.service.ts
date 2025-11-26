import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import * as amqp from 'amqp-connection-manager';
import { ChannelWrapper } from 'amqp-connection-manager';
import { ConfirmChannel } from 'amqplib';
import { RabbitMQConfig } from '../config/rabbitmq.config';

@Injectable()
export class RabbitMQService implements OnModuleInit, OnModuleDestroy {
  private connection: amqp.AmqpConnectionManager;
  private channelWrapper: ChannelWrapper;

  async onModuleInit() {
    this.connection = amqp.connect([RabbitMQConfig.url]);

    this.channelWrapper = this.connection.createChannel({
      json: true,
      setup: async (channel: ConfirmChannel) => {
        // Declare exchange
        await channel.assertExchange(
          RabbitMQConfig.exchanges.notifications,
          'direct',
          { durable: true }
        );

        // Declare queues
        await channel.assertQueue(RabbitMQConfig.queues.email, { durable: true });
        await channel.assertQueue(RabbitMQConfig.queues.push, { durable: true });
        await channel.assertQueue(RabbitMQConfig.queues.failed, { durable: true });

        // Bind queues to exchange
        await channel.bindQueue(
          RabbitMQConfig.queues.email,
          RabbitMQConfig.exchanges.notifications,
          RabbitMQConfig.routingKeys.email
        );

        await channel.bindQueue(
          RabbitMQConfig.queues.push,
          RabbitMQConfig.exchanges.notifications,
          RabbitMQConfig.routingKeys.push
        );

        await channel.bindQueue(
          RabbitMQConfig.queues.failed,
          RabbitMQConfig.exchanges.notifications,
          RabbitMQConfig.routingKeys.failed
        );
      },
    });

    await this.channelWrapper.waitForConnect();
    console.log('RabbitMQ connected and configured');
  }

  async publishToQueue(routingKey: string, message: any): Promise<void> {
    try {
      await this.channelWrapper.publish(
        RabbitMQConfig.exchanges.notifications,
        routingKey,
        message,
        { persistent: true }
      );
    } catch (error) {
      console.error('Failed to publish message:', error);
      throw error;
    }
  }

  async onModuleDestroy() {
    await this.channelWrapper.close();
    await this.connection.close();
  }
}