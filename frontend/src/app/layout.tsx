import type { Metadata } from 'next';
import { Geist } from 'next/font/google';
import AppShell from '@/components/AppShell';
import './globals.css';

const geist = Geist({ subsets: ['latin'], variable: '--font-geist', display: 'swap' });

export const metadata: Metadata = {
  title: { default: 'IP-SAKTI Intelligence', template: '%s | IP-SAKTI' },
  description:
    'Evidence-grounded intellectual property, traditional knowledge and regulatory screening workspace.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={geist.variable} suppressHydrationWarning>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
