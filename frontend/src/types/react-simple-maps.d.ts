declare module "react-simple-maps" {
  import type { ReactNode } from "react";

  export type GeographyProps = {
    geography: { rsmKey: string; properties?: Record<string, unknown> };
    onMouseEnter?: () => void;
    onMouseLeave?: () => void;
    onClick?: () => void;
    style?: Record<string, Record<string, string | number>>;
  };

  export function ComposableMap(props: { projection?: string; className?: string; children?: ReactNode }): JSX.Element;
  export function Geographies(props: {
    geography: string;
    children: (args: { geographies: GeographyProps["geography"][] }) => ReactNode;
  }): JSX.Element;
  export function Geography(props: GeographyProps): JSX.Element;
}
