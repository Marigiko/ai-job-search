import LinkedInAutomator from './linkedin.js';
import GetOnBoardAutomator from './getonbrd.js';
import ComputrabajoAutomator from './computrabajo.js';
import WeWorkRemotelyAutomator from './weworkremotely.js';
import TheMuseAutomator from './themuse.js';
import FreehireAutomator from './freehire.js';
import JobicyAutomator from './jobicy.js';
import RemotiveAutomator from './remotive.js';
import ATSGenericAutomator from './ats_generic.js';
import CompanySiteAutomator from './company_site.js';

export const AUTOMATORS = {
  linkedin: LinkedInAutomator,
  getonbrd: GetOnBoardAutomator,
  computrabajo: ComputrabajoAutomator,
  weworkremotely: WeWorkRemotelyAutomator,
  themuse: TheMuseAutomator,
  freehire: FreehireAutomator,
  jobicy: JobicyAutomator,
  remotive: RemotiveAutomator,
  ats_generic: ATSGenericAutomator,
  other: CompanySiteAutomator,
  company_site: CompanySiteAutomator,
  ashby: ATSGenericAutomator,
  freshteam: ATSGenericAutomator,
};

export const PORTAL_LABELS = {
  linkedin: 'LinkedIn',
  getonbrd: 'GetOnBoard',
  computrabajo: 'Computrabajo',
  weworkremotely: 'WeWorkRemotely',
  themuse: 'The Muse',
  freehire: 'freehire.dev',
  jobicy: 'Jobicy',
  remotive: 'Remotive',
  ats_generic: 'ATS (Greenhouse, Lever, etc.)',
  other: 'Other / Company Site',
  company_site: 'Company Site',
  ashby: 'Ashby',
  freshteam: 'FreshTeam',
};
