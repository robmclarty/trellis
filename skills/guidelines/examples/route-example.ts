// Example: Route definition pattern
// This shows the expected structure for an HTTP route handler.
// Validation is declared at the route level using Zod schemas.
// The handler receives typed, validated input and returns a typed response.

import { FastifyInstance } from "fastify";
import { z } from "zod";
import { findPassesByTeacher } from "../services/passes.js";

const querySchema = z.object({
  teacherId: z.string().uuid(),
  status: z.enum(["active", "completed", "expired"]).optional(),
  limit: z.coerce.number().int().min(1).max(100).default(25),
});

export const registerPassRoutes = (app: FastifyInstance) => {
  app.get("/passes", {
    schema: {
      querystring: querySchema,
    },
    handler: async (request, reply) => {
      const { teacherId, status, limit } = request.query as z.infer<typeof querySchema>;
      const passes = await findPassesByTeacher(teacherId, { status, limit });
      return reply.send({ data: passes });
    },
  });
};
