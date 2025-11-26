import {
  Controller,
  Post,
  Get,
  Body,
  Param,
  Query,
  UseGuards,
  Request
} from '@nestjs/common';
import { NotificationsService } from './notifications.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { SendNotificationDto } from './dto/send-notification.dto';
import { ApiResponse } from '../common/dto/response.dto';

@Controller('notifications')
@UseGuards(JwtAuthGuard)
export class NotificationsController {
  constructor(private notificationsService: NotificationsService) { }

  @Post()
  async sendNotification(@Body() dto: SendNotificationDto, @Request() req) {
    // Optional: Ensure authenticated user matches the user_id in request
    if (req.user.user_id !== dto.user_id) {
      return ApiResponse.error('Unauthorized to send notification for this user');
    }

    const notification = await this.notificationsService.sendNotification(dto);
    return ApiResponse.success('Notification queued successfully', notification);
  }

  @Get(':id')
  async getNotificationStatus(@Param('id') id: string) {
    const notification = await this.notificationsService.getNotificationStatus(id);
    return ApiResponse.success('Notification status retrieved', notification);
  }

  @Get('user/:userId')
  async getUserNotifications(
    @Param('userId') userId: string,
    @Query('page') page: string = '1',
    @Query('limit') limit: string = '10',
    @Request() req
  ) {
    if (req.user.user_id !== userId) {
      return ApiResponse.error('Unauthorized to view notifications for this user');
    }

    const pageNum = parseInt(page, 10);
    const limitNum = parseInt(limit, 10);

    const result = await this.notificationsService.getUserNotifications(
      userId,
      pageNum,
      limitNum
    );

    return ApiResponse.success(
      'User notifications retrieved',
      result.notifications,
      result.meta
    );
  }
}