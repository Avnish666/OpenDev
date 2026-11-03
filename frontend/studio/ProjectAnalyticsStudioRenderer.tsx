// This entry is resolved only by an explicitly enabled optional Studio build.
import { useMemo } from 'react';
import { AgStudio } from 'ag-studio-react';
import { AgStudioLicenseManager, type AgDataSourcesDefinition } from 'ag-studio';
import { studioData, type AnalyticsOverview } from '../src/api/analytics';
const key=import.meta.env.VITE_AG_STUDIO_LICENSE_KEY;
if(key)AgStudioLicenseManager.setLicenseKey(key);
export default function ProjectAnalyticsStudioRenderer({data}:{data:AnalyticsOverview}){
 const sources=useMemo<AgDataSourcesDefinition>(()=>({sources:studioData(data).sources.filter(source=>source.data.length>0)}),[data]);
 return <div style={{height:650,width:'100%'}} aria-label="AG Studio local report workspace"><AgStudio studioId="opendev-analytics" data={sources} mode="edit" /></div>;
}
