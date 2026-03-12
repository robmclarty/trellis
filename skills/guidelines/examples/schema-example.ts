// Example: Schema and data model pattern
// Drizzle table definitions paired with Zod schemas for validation.
// The Zod schema is the source of truth for input validation.
// Drizzle handles persistence; Zod handles boundaries.

import { pgTable, uuid, varchar, timestamp, pgEnum } from "drizzle-orm/pg-core";
import { z } from "zod";

// Drizzle enum + table definition
export const passStatusEnum = pgEnum("pass_status", [
  "active",
  "completed",
  "expired",
  "revoked",
]);

export const passes = pgTable("passes", {
  id: uuid("id").defaultRandom().primaryKey(),
  studentId: uuid("student_id").notNull(),
  teacherId: uuid("teacher_id").notNull(),
  destination: varchar("destination", { length: 255 }).notNull(),
  status: passStatusEnum("status").notNull().default("active"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  completedAt: timestamp("completed_at"),
});

// Zod schema for creating a pass (input validation at boundaries)
export const createPassSchema = z.object({
  studentId: z.string().uuid(),
  teacherId: z.string().uuid(),
  destination: z.string().min(1).max(255),
});

// Zod schema for the full pass shape (used for response typing)
export const passSchema = z.object({
  id: z.string().uuid(),
  studentId: z.string().uuid(),
  teacherId: z.string().uuid(),
  destination: z.string(),
  status: z.enum(["active", "completed", "expired", "revoked"]),
  createdAt: z.coerce.date(),
  completedAt: z.coerce.date().nullable(),
});
