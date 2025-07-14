import { BrowserRouter, Routes, Route } from "react-router-dom";
import MDrawer from "./pages/MDrawer.jsx";
import CssBaseline from "@mui/material/CssBaseline";
import { useState, useEffect } from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { Box } from "@mui/material";


function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setIsLoading(false);
    }, 1200);
    return () => {

    };
  }, []);

  const theme = createTheme({
    palette: {
      mode: darkMode ? "dark" : "light",
      primary: {
        
        main: "#1c42e8",
        light: "#fafafa",
        dark: "#003366",
        contrastText: "#fafafa",
      },
      secondary: {
        main: "#ecce3a",
        light: "#F06674",
        dark: "#A32228",
        contrastText: "#fafafa",
      },
      gray: {
        50: "#f5f5f5",
        100: "#eeeeee",
        200: "#e0e0e0",
        300: "#bdbdbd",
        400: "#9e9e9e",
        500: "#757575",
        600: "#616161",
        700: "#424242",
        800: "#212121",
        900: "#121212",
      },
    },
  });

  const handleDarkModeChange = () => {
    setDarkMode(!darkMode);
  };


  return (
    <>
      {isLoading ? (
        <Box
          sx={{
            height: "100vh",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
        </Box>
      ) : (
        <BrowserRouter>
          <div className="App">
            <ThemeProvider theme={theme}>
              <CssBaseline />
              <Routes>
                <Route path="/" element={<MDrawer onDarkModeChange={handleDarkModeChange} />}></Route>
                
              </Routes>
            </ThemeProvider>
          </div>
        </BrowserRouter>
      )}
    </>
  );
}

export default App;
