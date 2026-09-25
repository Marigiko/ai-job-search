import type { KanbanResponse } from "@/types/pipeline";

export const mockKanbanData: KanbanResponse = {
  stages: {
    discovered: [
      {
        job_id: 1,
        job_title: "Senior Backend Engineer",
        company_name: "TechCorp",
        application_id: null,
        status: "discovered",
        applied_date: null,
      },
      {
        job_id: 2,
        job_title: "Full Stack Developer",
        company_name: "StartupXYZ",
        application_id: null,
        status: "discovered",
        applied_date: null,
      },
      {
        job_id: 3,
        job_title: "Platform Engineer",
        company_name: "CloudScale",
        application_id: null,
        status: "discovered",
        applied_date: null,
      },
    ],
    interested: [
      {
        job_id: 4,
        job_title: "Staff Engineer",
        company_name: "DataFlow",
        application_id: 10,
        status: "interested",
        applied_date: null,
      },
    ],
    applied: [
      {
        job_id: 5,
        job_title: "Backend Lead",
        company_name: "FinServ",
        application_id: 11,
        status: "applied",
        applied_date: "2026-08-10",
      },
      {
        job_id: 6,
        job_title: "Distributed Systems Engineer",
        company_name: "RemoteFirst",
        application_id: 12,
        status: "applied",
        applied_date: "2026-08-08",
      },
    ],
    screening: [
      {
        job_id: 7,
        job_title: "Senior Python Developer",
        company_name: "AILabs",
        application_id: 13,
        status: "screening",
        applied_date: "2026-08-05",
      },
    ],
    interview: [
      {
        job_id: 8,
        job_title: "Engineering Manager",
        company_name: "GrowthCo",
        application_id: 14,
        status: "interview",
        applied_date: "2026-07-28",
      },
    ],
    offer: [],
    rejected: [
      {
        job_id: 9,
        job_title: "Frontend Developer",
        company_name: "WebAgency",
        application_id: 15,
        status: "rejected",
        applied_date: "2026-07-15",
      },
    ],
  },
};
