'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export const navigation:[string,string,string][] = [
 ['dashboard','Dashboard','⌂'], ['ask','Ask IP-SAKTI','◌'],
 ['patentability','Patentability','▤'], ['prior-art','Prior Art','⌕'], ['tk-risk','TK Risk','✦'],
 ['regulation-compare','Regulation Compare','⚖'], ['document-checker','Document Compliance','▧'], ['regulation-changes','Regulation Changes','↝'], ['compliance-journey','Compliance Journey','→'],
 ['knowledge-library','Knowledge Library','▱'], ['regulatory-alerts','Regulatory Alerts','!'], ['reports','Reports','▥'], ['settings','Settings','⚙'],
];

const groups = [
 ['INTELLIGENCE', ['dashboard','ask']],
 ['IP ANALYSIS', ['patentability','prior-art','tk-risk']],
 ['REGULATION', ['regulation-compare','document-checker','regulation-changes','compliance-journey','regulatory-alerts']],
 ['WORKSPACE', ['knowledge-library','reports','settings']],
] as const;

export default function Sidebar({open,onClose}:{open:boolean,onClose:()=>void}) {
 const path=usePathname();
 const isActive=(slug:string)=>path===`/${slug}` || (path==='/' && slug==='dashboard');
 return <>
  {open && <button className="nav-scrim visible" aria-label="Close navigation" onClick={onClose}/>}
  <aside className={`sidebar ${open?'open':''}`}>
   <Link href="/dashboard" className="brand" onClick={onClose}><span className="brand-mark"><i>IS</i></span><span>IP-SAKTI<small>Innovation <b>|</b> Evidence <b>|</b> Impact</small></span></Link>
   <nav aria-label="Main navigation">
    {groups.map(([group,slugs])=><section className="nav-group" key={group}><div className="nav-label">{group}</div>{slugs.map(slug=>{
      const item=navigation.find(n=>n[0]===slug)!;
      return <Link key={slug} href={`/${slug}`} onClick={onClose} aria-current={isActive(slug)?'page':undefined} className={isActive(slug)?'active':''} title={item[1]}><span className="nav-symbol" aria-hidden="true">{item[2]}</span><span>{item[1]}</span></Link>;
    })}</section>)}
   </nav>
   <div className="sidebar-foot"><span className="shield-icon">⌁</span><div><strong>Traditional Wisdom</strong><small>Smarter Tomorrow</small></div></div>
  </aside>
 </>;
}
