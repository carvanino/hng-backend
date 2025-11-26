import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { RabbitMQService } from '../rabbitmq/rabbitmq.service';
import { RabbitMQConfig } from '../config/rabbitmq.config';
import { SendNotificationDto } from './dto/send-notification.dto';

@Injectable()
export class NotificationsService {
  constructor(
    private prisma: PrismaService,
    private rabbitMQ: RabbitMQService,
  ) { }

  async sendNotification(dto: SendNotificationDto) {
    // Create notification record
    const notification = await this.prisma.notification.create({
      data: {
        user_id: dto.user_id,
        type: dto.type,
        template_id: dto.template_id,
        recipient: dto.recipient,
        subject: dto.subject,
        content: dto.content,
        metadata: dto.metadata || {},
        status: 'pending',
      },
    });

    // Prepare message for queue
    const message = {
      notification_id: notification.id,
      user_id: dto.user_id,
      type: dto.type,
      template_id: dto.template_id,
      recipient: dto.recipient,
      subject: dto.subject,
      content: dto.content,
      metadata: dto.metadata,
      created_at: notification.created_at,
    };

    // Route to appropriate queue
    const routingKey = dto.type === 'email'
      ? RabbitMQConfig.routingKeys.email
      : RabbitMQConfig.routingKeys.push;

    try {
      await this.rabbitMQ.publishToQueue(routingKey, message);
    } catch (error) {
      // Update notification status to failed
      await this.prisma.notification.update({
        where: { id: notification.id },
        data: {
          status: 'failed',
          error_message: 'Failed to queue notification',
        },
      });
      throw error;
    }

    return {
      id: notification.id,
      user_id: notification.user_id,
      type: notification.type,
      status: notification.status,
      recipient: notification.recipient,
      created_at: notification.created_at,
    };
  }

  async getNotificationStatus(id: string) {
    const notification = await this.prisma.notification.findUnique({
      where: { id },
      select: {
        id: true,
        user_id: true,
        type: true,
        status: true,
        recipient: true,
        subject: true,
        error_message: true,
        sent_at: true,
        delivered_at: true,
        created_at: true,
        updated_at: true,
      },
    });

    if (!notification) {
      throw new NotFoundException('Notification not found');
    }

    return notification;
  }

  async getUserNotifications(userId: string, page: number = 1, limit: number = 10) {
    const skip = (page - 1) * limit;

    const [notifications, total] = await Promise.all([
      this.prisma.notification.findMany({
        where: { user_id: userId },
        orderBy: { created_at: 'desc' },
        skip,
        take: limit,
        select: {
          id: true,
          type: true,
          status: true,
          recipient: true,
          subject: true,
          created_at: true,
        },
      }),
      this.prisma.notification.count({ where: { user_id: userId } }),
    ]);

    const total_pages = Math.ceil(total / limit);

    return {
      notifications,
      meta: {
        total,
        limit,
        page,
        total_pages,
        has_next: page < total_pages,
        has_previous: page > 1,
      },
    };
  }
}