// Estilos compartidos para los componentes del analizador de código
export const styles = {
    container: {
      mt: 4,
      mb: 4
    },
    header: {
      display: 'flex',
      alignItems: 'center',
      mb: 3
    },
    headerIcon: {
      mr: 2,
      color: 'primary.main',
      fontSize: 40
    },
    inputSection: {
      mb: 4
    },
    pathInput: {
      mb: 2
    },
    generateButton: {
      mt: 2
    },
    fileListContainer: {
      mt: 3,
      mb: 3
    },
    treeItem: {
      py: 0.5
    },
    nestedTreeItem: {
      pl: 4
    },
    loadingContainer: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      flexDirection: 'column',
      height: 200
    },
    statsCard: {
      mb: 3
    },
    treeViewContainer: {
      maxHeight: 400,
      overflow: 'auto',
      border: '1px solid #e0e0e0',
      borderRadius: 1,
      p: 1
    },
    tabContent: {
      p: 2,
      mt: 2
    },
    connectionLine: {
      position: 'relative',
      '&::before': {
        content: '""',
        position: 'absolute',
        left: -10,
        top: '50%',
        width: 20,
        height: 1,
        bgcolor: 'divider'
      }
    },
    dependencyItem: {
      mb: 1,
      p: 1.5,
      border: '1px solid',
      borderColor: 'divider',
      borderRadius: 1,
    },
    apiCard: {
      mb: 2,
      border: '1px solid',
      borderColor: 'divider'
    },
    parameterTag: {
      borderRadius: 1,
      fontSize: '0.75rem',
      p: 0.5,
      display: 'inline-block',
      mr: 1
    },
    infoCard: {
      mb: 2,
      bgcolor: 'info.light',
      color: 'info.contrastText'
    },
    grid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(2, 1fr)',
      gap: 2,
      mt: 2
    }
  };