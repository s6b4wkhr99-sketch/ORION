import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";

type LeFrameLogoProps = {
  variant?: "default" | "white";
  className?: string;
  link?: boolean;
  height?: number;
};

export function LeFrameLogo({
  variant = "default",
  className,
  link = false,
  height = 20,
}: LeFrameLogoProps) {
  const src =
    variant === "white"
      ? "/images/Le_Frame-logo-white.svg"
      : "/images/Le_Frame-logo.svg";

  const img = (
    <Image
      src={src}
      alt="Le Frame"
      width={Math.round(height * 2.5)}
      height={height}
      className={cn("w-auto", className)}
      style={{ height }}
      priority
    />
  );

  if (link) {
    return (
      <Link
        href="https://leframe.com"
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex shrink-0 items-center opacity-90 transition-opacity hover:opacity-100"
        aria-label="Le Frame"
      >
        {img}
      </Link>
    );
  }

  return <span className="inline-flex shrink-0 items-center">{img}</span>;
}
