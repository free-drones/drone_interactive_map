/**
 * Custom Material UI wrapper for setting primary color localy.
 * NOTE that this somewhat diverges from the Material Design styling methodology. Therefore, use with care.
 */

import React from 'react';
import { createMuiTheme, ThemeProvider } from '@material-ui/core/styles';

function ColorWrapper (props, ref) {
    
    // Map color="primary" to all children
    const children = React.Children.map(props.children, (child, index) => 
        React.cloneElement(child, {
            color: "primary", 
            ref: ref
        })
    );

    function generateThemeWrapper(baseTheme) {
        const extendedTheme = createMuiTheme({
            ...baseTheme,
            palette : {
                ...baseTheme.palette,
                // If given a hex color, use that. Else, assume string constant of base palette.
                primary : props.color.startsWith("#") ? {main: props.color} : baseTheme.palette[props.color],
            }
        });

        return extendedTheme;
    }

    return (
        <ThemeProvider theme={generateThemeWrapper}>
            {children}
        </ThemeProvider>
    );
}

export default React.forwardRef(ColorWrapper)