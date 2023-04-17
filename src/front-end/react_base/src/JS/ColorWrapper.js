/**
 * Custom Material UI wrapper for setting primary color locally.
 * NOTE that this somewhat diverges from the Material Design styling methodology. Therefore, use with care.
 */

import React from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { StyledEngineProvider } from "@mui/material";

function ColorWrapper(props, ref) {
  // Map color="primary" to all children
  const children = React.Children.map(props.children, (child, index) =>
    React.cloneElement(child, {
      color: "primary",
      ref: ref,
    })
  );

  function generateThemeWrapper(baseTheme) {
    const extendedTheme = createTheme({
      ...baseTheme,
      palette: {
        ...baseTheme.palette,
        // If given a hex color, use that. Else, assume string constant of base palette.
        primary: props.color.startsWith("#")
          ? { main: props.color }
          : baseTheme.palette[props.color],
      },
    });

    return extendedTheme;
  }

  return (
    <StyledEngineProvider injectFirst>
      <ThemeProvider theme={generateThemeWrapper}>{children}</ThemeProvider>
    </StyledEngineProvider>
  );
}

export default React.forwardRef(ColorWrapper);
