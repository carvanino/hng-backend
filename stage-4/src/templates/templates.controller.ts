import {
  Controller,
  Get,
  Post,
  Patch,
  Delete,
  Body,
  Param,
  Query,
  UseGuards
} from '@nestjs/common';
import { TemplatesService } from './templates.service';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CreateTemplateDto } from './dto/create-template.dto';
import { UpdateTemplateDto } from './dto/update-template.dto';
import { ApiResponse } from '../common/dto/response.dto';

@Controller('templates')
@UseGuards(JwtAuthGuard)
export class TemplatesController {
  constructor(private templatesService: TemplatesService) { }

  @Post()
  async create(@Body() dto: CreateTemplateDto) {
    const template = await this.templatesService.create(dto);
    return ApiResponse.success('Template created successfully', template);
  }

  @Get()
  async findAll(
    @Query('page') page: string = '1',
    @Query('limit') limit: string = '10',
    @Query('type') type?: string,
  ) {
    const pageNum = parseInt(page, 10);
    const limitNum = parseInt(limit, 10);

    const result = await this.templatesService.findAll(pageNum, limitNum, type);
    return ApiResponse.success('Templates retrieved successfully', result.templates, result.meta);
  }

  @Get(':id')
  async findOne(@Param('id') id: string) {
    const template = await this.templatesService.findOne(id);
    return ApiResponse.success('Template retrieved successfully', template);
  }

  @Get('name/:name')
  async findByName(@Param('name') name: string) {
    const template = await this.templatesService.findByName(name);
    return ApiResponse.success('Template retrieved successfully', template);
  }

  @Patch(':id')
  async update(@Param('id') id: string, @Body() dto: UpdateTemplateDto) {
    const template = await this.templatesService.update(id, dto);
    return ApiResponse.success('Template updated successfully', template);
  }

  @Delete(':id')
  async remove(@Param('id') id: string) {
    const result = await this.templatesService.remove(id);
    return ApiResponse.success('Template deleted successfully', result);
  }

  @Post(':id/render')
  async render(
    @Param('id') id: string,
    @Body() variables: Record<string, any>
  ) {
    const rendered = await this.templatesService.renderTemplate(id, variables);
    return ApiResponse.success('Template rendered successfully', rendered);
  }
}