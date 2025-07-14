import React from "react";
import {
  Grid,
  Paper,
  Typography,
  FormControl,
  Select,
  MenuItem,
} from "@mui/material";

const ConfiguracionesAvatar = ({
  config,
  selectedLocale,
  handleCharacterChange,
  handleStyleChange,
  handleLocaleChange,
  handleVoiceChange,
  avatarOptions,
  languageOptions,
  voices,
}) => {
  return (
    <Grid item xs={12}>
      <Paper elevation={3} sx={{ p: 2 }}>
        <Grid item xs={6} sx={{ mt: 2 }}>
          <Grid container>
            {/* Selector de Personaje */}
            <Grid item xs={3}>
              <FormControl fullWidth>
                <Typography sx={{ fontSize: "0.875rem", fontWeight: "800" }}>
                  Personaje del Avatar
                </Typography>
                <Select
                  sx={{ fontSize: "0.875rem" }}
                  value={config.avatarCharacter}
                  onChange={handleCharacterChange}
                >
                  {Object.keys(avatarOptions).map((character) => (
                    <MenuItem key={character} value={character}>
                      {character}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Selector de Estilo */}
            <Grid item xs={3}>
              <FormControl fullWidth>
                <Typography sx={{ fontSize: "0.875rem", fontWeight: "800" }}>
                  Estilo del Avatar
                </Typography>
                <Select
                  sx={{ fontSize: "0.875rem" }}
                  value={config.avatarStyle}
                  onChange={handleStyleChange}
                >
                  {(avatarOptions[config.avatarCharacter] || []).map(
                    (style) => (
                      <MenuItem key={style} value={style}>
                        {style}
                      </MenuItem>
                    )
                  )}
                </Select>
              </FormControl>
            </Grid>

            {/* Selector de Idioma */}
            <Grid item xs={3}>
              <FormControl fullWidth>
                <Typography sx={{ fontSize: "0.875rem", fontWeight: "800" }}>
                  Selecciona el idioma
                </Typography>
                <Select
                  sx={{ fontSize: "0.875rem" }}
                  value={selectedLocale}
                  onChange={handleLocaleChange}
                >
                  {languageOptions.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Selector de Voz */}
            <Grid item xs={3}>
              <FormControl fullWidth>
                <Typography sx={{ fontSize: "0.875rem", fontWeight: "800" }}>
                  Selecciona la voz
                </Typography>
                <Select
                  sx={{ fontSize: "0.875rem" }}
                  value={config.ttsVoice}
                  onChange={handleVoiceChange}
                >
                  {voices[selectedLocale].map((voice) => (
                    <MenuItem key={voice.value} value={voice.value}>
                      {voice.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Grid>
      </Paper>
    </Grid>
  );
};

export default ConfiguracionesAvatar;
