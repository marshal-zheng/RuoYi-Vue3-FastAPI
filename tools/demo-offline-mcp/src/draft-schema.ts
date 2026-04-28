import { z } from 'zod';

export const riskLevelSchema = z.enum(['low', 'medium', 'high']);
export const simulationStatusSchema = z.enum(['idle', 'running', 'paused', 'completed', 'failed']);

export const industryDataDraftSchema = z.object({
  industry: z.object({
    id: z.string().min(1),
    name: z.string().min(1),
    keywords: z.array(z.string().min(1)).optional(),
  }),
  scenario: z.object({
    id: z.string().min(1),
    name: z.string().min(1),
    version: z.string().min(1).optional(),
    seed: z.string().min(1).optional(),
    description: z.string().optional(),
  }),
  projects: z
    .array(
      z.object({
        key: z.string().min(1),
        name: z.string().min(1),
        region: z.string().optional(),
        stage: z.string().min(1),
        ownerRole: z.string().min(1),
        ownerName: z.string().optional(),
        riskLevel: riskLevelSchema,
        risk: z.string().min(1),
        remark: z.string().min(1),
        keyMetrics: z
          .array(
            z.object({
              name: z.string().min(1),
              value: z.string().min(1),
              trend: z.string().optional(),
            })
          )
          .optional(),
        versions: z
          .array(
            z.object({
              name: z.string().min(1),
              locked: z.boolean().optional(),
              summary: z.string().optional(),
            })
          )
          .optional(),
        topology: z
          .object({
            nodes: z
              .array(
                z.object({
                  name: z.string().min(1),
                  type: z.string().min(1),
                  status: z.string().optional(),
                })
              )
              .optional(),
            links: z
              .array(
                z.object({
                  source: z.string().min(1),
                  target: z.string().min(1),
                  label: z.string().optional(),
                })
              )
              .optional(),
          })
          .optional(),
        simulation: z
          .object({
            status: simulationStatusSchema.optional(),
            messages: z.array(z.string().min(1)).optional(),
            alarms: z
              .array(
                z.object({
                  severity: riskLevelSchema,
                  message: z.string().min(1),
                })
              )
              .optional(),
            events: z.array(z.string().min(1)).optional(),
          })
          .optional(),
      })
    )
    .min(1),
});
