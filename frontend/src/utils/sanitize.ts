/**
 * HTML Sanitization Utilities
 *
 * Prevents XSS attacks when rendering AI-generated or user-provided content.
 */

import DOMPurify from 'dompurify';

/**
 * Sanitize HTML content for safe rendering via dangerouslySetInnerHTML.
 *
 * Only allows basic formatting tags - no scripts, iframes, or event handlers.
 */
export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li', 'span'],
    ALLOWED_ATTR: ['class'],
  });
}

/**
 * Sanitize HTML with additional tags for report content.
 *
 * Allows headings, links (with restrictions), and tables for report rendering.
 */
export function sanitizeReportHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: [
      'b', 'i', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li', 'span',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'blockquote', 'code', 'pre',
    ],
    ALLOWED_ATTR: ['class', 'href', 'target', 'rel'],
    // Force safe link behavior
    ADD_ATTR: ['target', 'rel'],
    FORBID_TAGS: ['script', 'style', 'iframe', 'form', 'input'],
    FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover'],
  });
}
