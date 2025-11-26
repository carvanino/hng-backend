import { Injectable, NotFoundException, ConflictException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { UpdateUserDto } from './dto/update-user.dto';
import { AddPushTokenDto } from './dto/add-push-token.dto';
import { UpdatePreferencesDto } from './dto/update-preferences.dto';

@Injectable()
export class UsersService {
  constructor(private prisma: PrismaService) { }

  async findOne(id: string) {
    const user = await this.prisma.user.findUnique({
      where: { id },
      select: {
        id: true,
        email: true,
        created_at: true,
        updated_at: true,
        push_tokens: true,
        notification_preferences: true,
      },
    });

    if (!user) {
      throw new NotFoundException('User not found');
    }

    return user;
  }

  async update(id: string, dto: UpdateUserDto) {
    const user = await this.prisma.user.findUnique({ where: { id } });

    if (!user) {
      throw new NotFoundException('User not found');
    }

    if (dto.email) {
      const existingUser = await this.prisma.user.findUnique({
        where: { email: dto.email },
      });

      if (existingUser && existingUser.id !== id) {
        throw new ConflictException('Email already in use');
      }
    }

    return this.prisma.user.update({
      where: { id },
      data: dto,
      select: {
        id: true,
        email: true,
        updated_at: true,
      },
    });
  }

  async remove(id: string) {
    const user = await this.prisma.user.findUnique({ where: { id } });

    if (!user) {
      throw new NotFoundException('User not found');
    }

    await this.prisma.user.delete({ where: { id } });

    return { id };
  }

  async addPushToken(userId: string, dto: AddPushTokenDto) {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });

    if (!user) {
      throw new NotFoundException('User not found');
    }

    const existingToken = await this.prisma.pushToken.findUnique({
      where: { token: dto.token },
    });

    if (existingToken) {
      throw new ConflictException('Push token already exists');
    }

    return this.prisma.pushToken.create({
      data: {
        user_id: userId,
        token: dto.token,
        device_type: dto.device_type,
      },
    });
  }

  async removePushToken(userId: string, tokenId: string) {
    const pushToken = await this.prisma.pushToken.findUnique({
      where: { id: tokenId },
    });

    if (!pushToken) {
      throw new NotFoundException('Push token not found');
    }

    if (pushToken.user_id !== userId) {
      throw new NotFoundException('Push token not found for this user');
    }

    await this.prisma.pushToken.delete({ where: { id: tokenId } });

    return { id: tokenId };
  }

  async getPreferences(userId: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      include: { notification_preferences: true },
    });

    if (!user) {
      throw new NotFoundException('User not found');
    }

    if (!user.notification_preferences) {
      throw new NotFoundException('Preferences not found');
    }

    return user.notification_preferences;
  }

  async updatePreferences(userId: string, dto: UpdatePreferencesDto) {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });

    if (!user) {
      throw new NotFoundException('User not found');
    }

    return this.prisma.notificationPreference.upsert({
      where: { user_id: userId },
      update: dto,
      create: {
        user_id: userId,
        ...dto,
      },
    });
  }
}