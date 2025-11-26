import { IsString, IsIn, IsArray, IsOptional, IsBoolean } from 'class-validator';

export class UpdateTemplateDto {
  @IsString()
  @IsOptional()
  name?: string;

  @IsString()
  @IsIn(['email', 'push'])
  @IsOptional()
  type?: string;

  @IsString()
  @IsOptional()
  subject?: string;

  @IsString()
  @IsOptional()
  body?: string;

  @IsArray()
  @IsString({ each: true })
  @IsOptional()
  variables?: string[];

  @IsString()
  @IsOptional()
  language?: string;

  @IsBoolean()
  @IsOptional()
  is_active?: boolean;
}