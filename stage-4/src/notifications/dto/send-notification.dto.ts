import {
  IsString,
  IsNotEmpty,
  IsIn,
  IsOptional,
  IsObject
} from 'class-validator';

export class SendNotificationDto {
  @IsString()
  @IsNotEmpty()
  user_id!: string;

  @IsString()
  @IsIn(['email', 'push'])
  type!: string;

  @IsString()
  @IsOptional()
  template_id?: string;

  @IsString()
  @IsNotEmpty()
  recipient!: string; // email address or device token

  @IsString()
  @IsOptional()
  subject?: string; // for email notifications

  @IsString()
  @IsNotEmpty()
  content!: string;

  @IsObject()
  @IsOptional()
  metadata?: Record<string, any>;
}