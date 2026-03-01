import { defineCollection, z } from 'astro:content';

// Content schema for knowledge base articles
const contentSchema = z.object({
  // Required fields
  title: z.string().max(200),
  domain: z.enum(['ai', 'blockchain', 'protocol']),
  level: z.enum(['beginner', 'intermediate', 'master']),
  category: z.enum(['articles', 'tool', 'resource', 'video', 'audio', 'podcast', 'youtube', 'arxiv']),
  tags: z.array(z.string()).max(10).default([]),
  
  // Metadata
  created: z.date().or(z.string()).optional(),
  updated: z.date().or(z.string()).optional(),
  sources: z.array(z.object({
    url: z.string().url(),
    title: z.string(),
    accessed_at: z.string().optional(),
  })).min(1),
  
  // Review status
  aiReviewed: z.boolean().default(true),
  humanReviewed: z.boolean().default(false),
  status: z.enum(['pending-review', 'approved', 'rejected', 'published']).default('pending-review'),
  
  // Optional fields
  description: z.string().max(500).optional(),
  author: z.string().optional(),
  reviewer: z.string().optional(),
  credibilityScore: z.number().min(1).max(10).optional(),
  
  // Media fields
  mediaUrl: z.string().optional(),
  mediaType: z.enum(['text', 'video', 'audio']).optional(),
  
  // Progression/Learning path fields
  series: z.string().optional(),
  sequence: z.number().optional(),
  prerequisites: z.array(z.string()).optional(),
  next: z.string().optional(),
  learningOutcomes: z.array(z.string()).optional(),
});

// Define collections for each domain
const aiContent = defineCollection({
  type: 'content',
  schema: contentSchema,
});

const blockchainContent = defineCollection({
  type: 'content',
  schema: contentSchema,
});

const protocolContent = defineCollection({
  type: 'content',
  schema: contentSchema,
});

export const collections = {
  'ai': aiContent,
  'blockchain': blockchainContent,
  'protocol': protocolContent,
};
