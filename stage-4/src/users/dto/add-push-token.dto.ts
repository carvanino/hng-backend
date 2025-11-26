import { IsNotEmpty, IsString, IsIn } from 'class-validator';

export class AddPushTokenDto {
  @IsString()
  @IsNotEmpty()
  token!: string;

  @IsString()
  @IsIn(['ios', 'android', 'web'])
  device_type!: string;
}