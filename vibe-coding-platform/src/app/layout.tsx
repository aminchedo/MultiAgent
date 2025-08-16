import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter',
})

const jetbrainsMono = JetBrains_Mono({ 
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
})

export const metadata: Metadata = {
  title: 'Vibe Coding Platform - Revolutionary AI Code Generation',
  description: 'Describe your vibe, watch AI agents collaborate to build your complete project. The future of coding is here.',
  keywords: 'AI coding, code generation, development platform, artificial intelligence, programming',
  authors: [{ name: 'Vibe Coding Platform' }],
  creator: 'Vibe Coding Platform',
  openGraph: {
    title: 'Vibe Coding Platform - Revolutionary AI Code Generation',
    description: 'Describe your vibe, watch AI agents collaborate to build your complete project.',
    type: 'website',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Vibe Coding Platform',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Vibe Coding Platform',
    description: 'Revolutionary AI Code Generation Platform',
    images: ['/og-image.png'],
  },
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/site.webmanifest',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
