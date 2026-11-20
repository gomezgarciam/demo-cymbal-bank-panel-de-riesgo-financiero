import type { Metadata } from "next";
import { Inter, Roboto } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-inter",
  display: "swap",
});

const roboto = Roboto({
  subsets: ["latin"],
  weight: ["300", "400", "500", "700"],
  variable: "--font-roboto",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Cymbal Bank — Panel de Riesgo Financiero (MVP v1.0)",
  description:
    "Consola ejecutiva multimoneda (USD/EUR/MXN/COP) de Banca Corporativa y Gestión de Riesgos de Cymbal Bank: KPIs de cartera, motor de estrés EL/NPL/PD/LGD con precisión Decimal, alertas de morosidad y auditoría bancaria.",
  icons: {
    icon: "/logos/cymbal-bank-isotipo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className={`${inter.variable} ${roboto.variable}`}>
      <body>{children}</body>
    </html>
  );
}
