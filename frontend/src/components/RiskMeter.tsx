import ConfidenceScore from './ConfidenceScore';
export default function RiskMeter({score,label='Detected overlap',level}:{score:unknown,label?:string,level?:string}) {return <div className="risk-score"><ConfidenceScore score={score} label={label} description={level?.replaceAll('_',' ') || 'No clearance or novelty conclusion is implied.'}/></div>;}
