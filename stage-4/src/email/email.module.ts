import { Module } from '@nestjs/common';
import { EmailService } from './email.service';
import { TemplatesModule } from '../templates/templates.module';

@Module({
  imports: [TemplatesModule],
  providers: [EmailService],
})
export class EmailModule { }