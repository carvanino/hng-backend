import {
  Controller,
  Get,
  Patch,
  Delete,
  Post,
  Body,
  Param,
  UseGuards,
  Request
} from '@nestjs/common';
import { UsersService } from './users.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { UpdateUserDto } from './dto/update-user.dto';
import { AddPushTokenDto } from './dto/add-push-token.dto';
import { UpdatePreferencesDto } from './dto/update-preferences.dto';
import { ApiResponse } from '../common/dto/response.dto';

@Controller('users')
@UseGuards(JwtAuthGuard)
export class UsersController {
  constructor(private usersService: UsersService) { }

  @Get(':id')
  async findOne(@Param('id') id: string) {
    const user = await this.usersService.findOne(id);
    return ApiResponse.success('User retrieved successfully', user);
  }

  @Patch(':id')
  async update(@Param('id') id: string, @Body() dto: UpdateUserDto, @Request() req) {
    // Optional: Ensure users can only update their own profile
    if (req.user.user_id !== id) {
      return ApiResponse.error('Unauthorized to update this user');
    }

    const user = await this.usersService.update(id, dto);
    return ApiResponse.success('User updated successfully', user);
  }

  @Delete(':id')
  async remove(@Param('id') id: string, @Request() req) {
    // Optional: Ensure users can only delete their own profile
    if (req.user.user_id !== id) {
      return ApiResponse.error('Unauthorized to delete this user');
    }

    const result = await this.usersService.remove(id);
    return ApiResponse.success('User deleted successfully', result);
  }

  @Post(':id/push-tokens')
  async addPushToken(
    @Param('id') id: string,
    @Body() dto: AddPushTokenDto,
    @Request() req
  ) {
    if (req.user.user_id !== id) {
      return ApiResponse.error('Unauthorized to add push token for this user');
    }

    const token = await this.usersService.addPushToken(id, dto);
    return ApiResponse.success('Push token added successfully', token);
  }

  @Delete(':id/push-tokens/:tokenId')
  async removePushToken(
    @Param('id') id: string,
    @Param('tokenId') tokenId: string,
    @Request() req
  ) {
    if (req.user.user_id !== id) {
      return ApiResponse.error('Unauthorized to remove push token for this user');
    }

    const result = await this.usersService.removePushToken(id, tokenId);
    return ApiResponse.success('Push token removed successfully', result);
  }

  @Get(':id/preferences')
  async getPreferences(@Param('id') id: string, @Request() req) {
    if (req.user.user_id !== id) {
      return ApiResponse.error('Unauthorized to view preferences for this user');
    }

    const preferences = await this.usersService.getPreferences(id);
    return ApiResponse.success('Preferences retrieved successfully', preferences);
  }

  @Patch(':id/preferences')
  async updatePreferences(
    @Param('id') id: string,
    @Body() dto: UpdatePreferencesDto,
    @Request() req
  ) {
    if (req.user.user_id !== id) {
      return ApiResponse.error('Unauthorized to update preferences for this user');
    }

    const preferences = await this.usersService.updatePreferences(id, dto);
    return ApiResponse.success('Preferences updated successfully', preferences);
  }
}