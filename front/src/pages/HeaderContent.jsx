
import {  Grid, Paper } from "@mui/material";
import Typography from "@mui/material/Typography";
import { format } from 'date-fns';
import { useTheme } from "@mui/material/styles";
const HeaderContent = (props) => {
  const {titulo}=props
  // Obtener la fecha actual
  const date = new Date();
  const theme = useTheme();
  // Formatear la fecha en el formato deseado
  const formatDate = format(date, "d-MMMM-yyyy");


  return (

        <Paper
          sx={{
            padding: "10px",
            height: "30px%",
            backgroundColor: theme.palette.primary.light,
            color:theme.palette.primary.contrastText,

          }}
        >
          <Grid
            container
            display={"flex"}
            alignItems="center"
            justifyContent="space-between"
          >
            <Grid item>
              <Typography variant="h6">{titulo}</Typography>
            </Grid>
            <Grid item>
              <Typography variant="h6">{formatDate}</Typography>

            </Grid>
          </Grid>
        </Paper>

  );
};

export default HeaderContent;
