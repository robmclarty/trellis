/**
 * Example: Service function pattern
 * Service functions are plain exported functions, not class methods.
 * They receive explicit dependencies (db handle, config) as parameters.
 * They return Result types or throw only at system boundaries.
 * Business logic lives here, not in route handlers.
 */

import { eq, and, desc } from "drizzle-orm";
import { passes } from "../schema/passes.js";
import type { DbClient } from "../db/client.js";

type FindPassesOptions = {
  status?: "active" | "completed" | "expired";
  limit?: number;
};

export const findPassesByTeacher = async (
  db: DbClient,
  teacherId: string,
  options: FindPassesOptions = {},
) => {
  const { status, limit = 25 } = options;

  const conditions = [eq(passes.teacherId, teacherId)];
  if (status) {
    conditions.push(eq(passes.status, status));
  }

  return db
    .select()
    .from(passes)
    .where(and(...conditions))
    .orderBy(desc(passes.createdAt))
    .limit(limit);
};

export const completePass = async (db: DbClient, passId: string) => {
  const [updated] = await db
    .update(passes)
    .set({
      status: "completed",
      completedAt: new Date(),
    })
    .where(and(eq(passes.id, passId), eq(passes.status, "active")))
    .returning();

  if (!updated) {
    return { ok: false, reason: "pass_not_found_or_not_active" } as const;
  }

  return { ok: true, pass: updated } as const;
};
