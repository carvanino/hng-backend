export interface PaginationMeta {
  total: number;
  limit: number;
  page: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export class PaginationDto {
  page?: number = 1;
  limit?: number = 10;
}