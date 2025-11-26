import {
  IsBoolean,
  IsOptional,
  IsString,
  IsIn,
  IsInt,
  Min,
  Max
} from 'class-validator';

export class UpdatePreferencesDto {
  @IsBoolean()
  @IsOptional()
  email_enabled?: boolean;

  @IsBoolean()
  @IsOptional()
  push_enabled?: boolean;

  @IsString()
  @IsIn(['instant', 'daily', 'weekly'])
  @IsOptional()
  frequency?: string;

  @IsInt()
  @Min(0)
  @Max(23)
  @IsOptional()
  quiet_hours_start?: number;

  @IsInt()
  @Min(0)
  @Max(23)
  @IsOptional()
  quiet_hours_end?: number;
}