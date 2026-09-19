import type { Metadata } from 'next';
import AppShell from '@/components/AppShell';
import './globals.css';
export const metadata:Metadata={title:{default:'IP-SAKTI Intelligence',template:'%s | IP-SAKTI'},description:'Evidence-grounded intellectual property, traditional knowledge and regulatory screening workspace.'};
export default function RootLayout({children}:{children:React.ReactNode}) {return <html lang="en"><body><AppShell>{children}</AppShell></body></html>;}
