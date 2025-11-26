import { Injectable, NotFoundException, ConflictException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateTemplateDto } from './dto/create-template.dto';
import { UpdateTemplateDto } from './dto/update-template.dto';

@Injectable()
export class TemplatesService {
  constructor(private prisma: PrismaService) { }

  async create(dto: CreateTemplateDto) {
    const existingTemplate = await this.prisma.template.findUnique({
      where: { name: dto.name },
    });

    if (existingTemplate) {
      throw new ConflictException('Template with this name already exists');
    }

    return this.prisma.template.create({
      data: {
        name: dto.name,
        type: dto.type,
        subject: dto.subject,
        body: dto.body,
        variables: dto.variables,
        language: dto.language || 'en',
        is_active: dto.is_active ?? true,
      },
    });
  }

  async findAll(page: number = 1, limit: number = 10, type?: string) {
    const skip = (page - 1) * limit;

    const where = type ? { type } : {};

    const [templates, total] = await Promise.all([
      this.prisma.template.findMany({
        where,
        orderBy: { created_at: 'desc' },
        skip,
        take: limit,
      }),
      this.prisma.template.count({ where }),
    ]);

    const total_pages = Math.ceil(total / limit);

    return {
      templates,
      meta: {
        total,
        limit,
        page,
        total_pages,
        has_next: page < total_pages,
        has_previous: page > 1,
      },
    };
  }

  async findOne(id: string) {
    const template = await this.prisma.template.findUnique({
      where: { id },
    });

    if (!template) {
      throw new NotFoundException('Template not found');
    }

    return template;
  }

  async findByName(name: string) {
    const template = await this.prisma.template.findUnique({
      where: { name },
    });

    if (!template) {
      throw new NotFoundException('Template not found');
    }

    return template;
  }

  async update(id: string, dto: UpdateTemplateDto) {
    const template = await this.prisma.template.findUnique({
      where: { id },
    });

    if (!template) {
      throw new NotFoundException('Template not found');
    }

    if (dto.name && dto.name !== template.name) {
      const existingTemplate = await this.prisma.template.findUnique({
        where: { name: dto.name },
      });

      if (existingTemplate) {
        throw new ConflictException('Template with this name already exists');
      }
    }

    // Increment version on update
    return this.prisma.template.update({
      where: { id },
      data: {
        ...dto,
        version: template.version + 1,
      },
    });
  }

  async remove(id: string) {
    const template = await this.prisma.template.findUnique({
      where: { id },
    });

    if (!template) {
      throw new NotFoundException('Template not found');
    }

    await this.prisma.template.delete({ where: { id } });

    return { id };
  }

  async renderTemplate(templateId: string, variables: Record<string, any>): Promise<{ subject?: string; body: string }> {
    const template = await this.findOne(templateId);

    if (!template.is_active) {
      throw new ConflictException('Template is not active');
    }

    // Check if all required variables are provided
    const templateVars = template.variables as string[];
    const missingVars = templateVars.filter(v => !(v in variables));

    if (missingVars.length > 0) {
      throw new ConflictException(`Missing required variables: ${missingVars.join(', ')}`);
    }

    // Replace variables in body (supports {{variable}} format)
    let renderedBody = template.body;
    let renderedSubject = template.subject;

    for (const [key, value] of Object.entries(variables)) {
      const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
      renderedBody = renderedBody.replace(regex, String(value));
      if (renderedSubject) {
        renderedSubject = renderedSubject.replace(regex, String(value));
      }
    }

    return {
      subject: renderedSubject || undefined,
      body: renderedBody,
    };
  }
}