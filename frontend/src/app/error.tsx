'use client';
export default function Error({reset}:{reset:()=>void}){return <section className="panel"><h1>This page could not be displayed</h1><p>No successful assessment is asserted. Reload the page or check backend configuration.</p><button className="button primary" onClick={reset}>Try again</button></section>;}
