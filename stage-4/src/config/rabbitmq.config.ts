export const RabbitMQConfig = {
  url: process.env.RABBITMQ_URL || 'amqp://rabbitmq:rabbitmq@localhost:5672',
  exchanges: {
    notifications: 'notifications.direct',
  },
  queues: {
    email: 'email.queue',
    push: 'push.queue',
    failed: 'failed.queue',
  },
  routingKeys: {
    email: 'email',
    push: 'push',
    failed: 'failed',
  },
};