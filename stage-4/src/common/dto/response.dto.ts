import { PaginationMeta } from './pagination.dto';

export class ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message: string;
  meta?: PaginationMeta;

  constructor(success: boolean, message: string, data?: T, error?: string, meta?: PaginationMeta) {
    this.success = success;
    this.message = message;
    this.data = data;
    this.error = error;
    this.meta = meta;
  }

  static success<T>(message: string, data?: T, meta?: PaginationMeta): ApiResponse<T> {
    return new ApiResponse<T>(true, message, data, undefined, meta);
  }

  static error<T>(message: string, error?: string): ApiResponse<T> {
    return new ApiResponse<T>(false, message, undefined, error);
  }
}