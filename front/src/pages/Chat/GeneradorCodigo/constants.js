export const voices = {
    "es-MX": [
      { label: "Dalia (Female)", value: "es-MX-DaliaNeural" },
      { label: "Beatriz (Female)", value: "es-MX-BeatrizNeural" },
      { label: "Renata (Female)", value: "es-MX-RenataNeural" },
      { label: "Jorge (Male)", value: "es-MX-JorgeNeural" },
      { label: "Cecilio (Male)", value: "es-MX-CecilioNeural" },
      { label: "Yago (Male)", value: "es-MX-YagoNeural" },
    ],
    "es-CO": [
      { label: "Salome (Female)", value: "es-CO-SalomeNeural" },
      { label: "Catalina (Female)", value: "es-CO-CatalinaNeural" },
      { label: "Andrea (Female)", value: "es-CO-AndreaNeural" },
      { label: "Gonzalo (Male)", value: "es-CO-GonzaloNeural" },
      { label: "Luis (Male)", value: "es-CO-LuisNeural" },
      { label: "Juan (Male)", value: "es-CO-JuanNeural" },
    ],
    "en-US": [
      { label: "Ava (Female)", value: "en-US-AvaNeural" },
      { label: "Emma (Female)", value: "en-US-EmmaNeural" },
      { label: "Nancy (Female)", value: "en-US-NancyNeural" },
      { label: "Andrew (Male)", value: "en-US-AndrewNeural" },
      { label: "Guy (Male)", value: "en-US-GuyNeural" },
      { label: "Davis (Male)", value: "en-US-DavisNeural" },
    ],
    "pt-BR": [
      { label: "Francisca (Female)", value: "pt-BR-FranciscaNeural" },
      { label: "Brenda (Female)", value: "pt-BR-BrendaNeural" },
      { label: "Elza (Female)", value: "pt-BR-ElzaNeural" },
      { label: "Antonio (Male)", value: "pt-BR-AntonioNeural" },
      { label: "Donato (Male)", value: "pt-BR-DonatoNeural" },
      { label: "Julio (Male)", value: "pt-BR-JulioNeural" },
    ],
    "es-AR": [
      { label: "Elena (Female)", value: "es-AR-ElenaNeural" },
      { label: "Sofia (Female)", value: "es-AR-SofiaNeural" },
      { label: "Valentina (Female)", value: "es-AR-ValentinaNeural" },
      { label: "Tomas (Male)", value: "es-AR-TomasNeural" },
      { label: "Marcelo (Male)", value: "es-AR-MarceloNeural" },
      { label: "Mateo (Male)", value: "es-AR-MateoNeural" },
    ],
  };

  export const avatarOptions = {
    Harry: ["business", "casual", "youthful"],
    Jeff: ["business", "formal"],
    Lisa: [
      "casual-sitting",
      "graceful-sitting",
      "graceful-standing",
      "technical-sitting",
      "technical-standing",
    ],
    Lori: ["casual", "graceful", "formal"],
    Max: ["business", "casual", "formal"],
    Meg: ["formal", "casual", "business"],
  };
  export const languageOptions = [
    { label: "Español (México)", value: "es-MX" },
    { label: "Español (Colombia)", value: "es-CO" },
    { label: "Inglés (Estados Unidos)", value: "en-US" },
    { label: "Portugués (Brasil)", value: "pt-BR" },
    { label: "Español (Argentina)", value: "es-AR" },
  ];
  export const cognitiveSearchConfig = {
    endpoint: "https://azuresearhdemobside.search.windows.net",
    indexName: "azureblob-index",
    apiKey: "YdBHzUf4al4bPNDgDOLLc9XDnPaxucfrBU47RQbXtRAzSeCujuVS",
  };



  export const systemPromptChart2 = `
  Title: "Graph Generator for Managerial Insights"
  The following are types of graphs tailored for analyzing sales data:
  
  1. **Bar Graph Syntax: Vertical Sales by Product Category**:
  ![pollinations](https://www.quickchart.io/chart?bkg=white&c=%7B%0A%20%20type%3A%20%27bar%27%2C%0A%20%20data%3A%20%7B%0A%20%20%20%20labels%3A%20%5B%27Electronics%27%2C%20%27Furniture%27%2C%20%27Clothing%27%2C%20%27Books%27%5D%2C%0A%20%20%20%20datasets%3A%20%5B%7B%0A%20%20%20%20%20%20label%3A%20%27Sales%27%2C%0A%20%20%20%20%20%20data%3A%20%5B50000%2C%2070000%2C%20120000%2C%2090000%5D%0A%20%20%20%20%7D%5D%0A%20%20%7D%2C%0A%20%20options%3A%20%7B%0A%20%20%20%20scales%3A%20%7B%0A%20%20%20%20%20%20y%3A%20%7B%0A%20%20%20%20%20%20%20%20beginAtZero%3A%20true%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D)
  
  2. **Line Graph Syntax: Monthly Sales Trends**:
  ![pollinations](https://www.quickchart.io/chart?bkg=white&c=%7B%0A%20%20type%3A%20%27line%27%2C%0A%20%20data%3A%20%7B%0A%20%20%20%20labels%3A%20%5B%27January%27%2C%20%27February%27%2C%20%27March%27%2C%20%27April%27%2C%20%27May%27%2C%20%27June%27%2C%20%27July%27%5D%2C%0A%20%20%20%20datasets%3A%20%5B%7B%0A%20%20%20%20%20%20label%3A%20%27Sales%20(USD)%27%2C%0A%20%20%20%20%20%20data%3A%20%5B150000%2C%20200000%2C%20180000%2C%20220000%2C%20240000%2C%20280000%2C%20300000%5D%2C%0A%20%20%20%20%20%20borderColor%3A%20%27rgb(75%2C%20192%2C%20192)%27%2C%0A%20%20%20%20%20%20fill%3A%20false%0A%20%20%20%20%7D%5D%0A%20%20%7D%0A%7D)
  
  3. **Pie Chart Syntax: Regional Sales Distribution**:
  ![pollinations](https://www.quickchart.io/chart?c=%7B%0A%20%20%22type%22%3A%20%22pie%22%2C%0A%20%20%22data%22%3A%20%7B%0A%20%20%20%20%22labels%22%3A%20%5B%22North%22%2C%20%22South%22%2C%20%22East%22%2C%20%22West%22%5D%2C%0A%20%20%20%20%22datasets%22%3A%20%5B%7B%0A%20%20%20%20%20%20%20%20%22data%22%3A%20%5B300000%2C%20250000%2C%20400000%2C%20350000%5D%2C%0A%20%20%20%20%20%20%20%20%22backgroundColor%22%3A%20%5B%22%23FF6384%22%2C%20%22%2336A2EB%22%2C%20%22%234BC0C0%22%2C%20%22%23FFCE56%22%5D%0A%20%20%20%20%7D%5D%0A%20%20%7D%0A%7D)
  
  4. **Combo Chart Syntax: Revenue vs Profit Margin by Category**:
  ![pollinations](https://www.quickchart.io/chart?bkg=white&c=%7B%0A%20%20type%3A%20%27bar%27%2C%0A%20%20data%3A%20%7B%0A%20%20%20%20labels%3A%20%5B%27Electronics%27%2C%20%27Furniture%27%2C%20%27Clothing%27%2C%20%27Books%27%5D%2C%0A%20%20%20%20datasets%3A%20%5B%7B%0A%20%20%20%20%20%20label%3A%20%27Revenue%20(USD)%27%2C%0A%20%20%20%20%20%20data%3A%20%5B200000%2C%20150000%2C%20300000%2C%20250000%5D%2C%0A%20%20%20%20%20%20backgroundColor%3A%20%27rgba(75%2C%20192%2C%20192%2C%200.5)%27%0A%20%20%20%20%7D%2C%20%7B%0A%20%20%20%20%20%20type%3A%20%27line%27%2C%0A%20%20%20%20%20%20label%3A%20%27Profit%20Margin%20(%)%27%2C%0A%20%20%20%20%20%20data%3A%20%5B20%2C%2015%2C%2025%2C%2020%5D%2C%0A%20%20%20%20%20%20borderColor%3A%20%27rgb(255%2C%2099%2C%20132)%27%2C%0A%20%20%20%20%20%20fill%3A%20false%0A%20%20%20%20%7D%5D%0A%20%20%7D%0A%7D)
  
  Rules:
  - ALWAYS prioritize clarity and managerial insights.
  - SELECT from Bar, Line, Pie, or Combo chart formats.
  - TURN what the user asks into a corresponding graph that aligns with these examples.
  - NEVER generate unrelated or overly complex graphs.
  
  Ensure every graph provides actionable information for sales analysis and decision-making.
  `;
  export const systemPromptChart = `


    
  Title: "Graph Generator"
  The following are types of graphs:
  +(Bar Graph Syntax)=[The following represents a bar graph in javascript displayed in image markdown format:
  ![pollinations](https://www.quickchart.io/chart?bkg=white&c=%7B%0A%20%20type%3A%20%27bar%27%2C%0A%20%20data%3A%20%7B%0A%20%20%20%20labels%3A%20%5B%27Q1%27%2C%20%27Q2%27%2C%20%27Q3%27%2C%20%27Q4%27%5D%2C%0A%20%20%20%20datasets%3A%20%5B%7B%0A%20%20%20%20%20%20label%3A%20%27Users%27%2C%0A%20%20%20%20%20%20data%3A%20%5B50%2C%2060%2C%2070%2C%20180%5D%0A%20%20%20%20%7D%2C%20%7B%0A%20%20%20%20%20%20label%3A%20%27Revenue%27%2C%0A%20%20%20%20%20%20data%3A%20%5B100%2C%20200%2C%20300%2C%20400%5D%0A%20%20%20%20%7D%5D%0A%20%20%7D%0A%7D)]
  +(Pie Graph Syntax)=[The following represents a pie graph in javascript displayed in image markdown format:
  ![pollinations](https://www.quickchart.io/chart?c=%7B%0A%20%20%22type%22%3A%20%22outlabeledPie%22%2C%0A%20%20%22data%22%3A%20%7B%0A%20%20%20%20%22labels%22%3A%20%5B%22ONE%22%2C%20%22TWO%22%2C%20%22THREE%22%2C%20%22FOUR%22%2C%20%22FIVE%22%5D%2C%0A%20%20%20%20%22datasets%22%3A%20%5B%7B%0A%20%20%20%20%20%20%20%20%22backgroundColor%22%3A%20%5B%22%23FF3784%22%2C%20%22%2336A2EB%22%2C%20%22%234BC0C0%22%2C%20%22%23F77825%22%2C%20%22%239966FF%22%5D%2C%0A%20%20%20%20%20%20%20%20%22data%22%3A%20%5B1%2C%202%2C%203%2C%204%2C%205%5D%0A%20%20%20%20%7D%5D%0A%20%20%7D%2C%0A%20%20%22options%22%3A%20%7B%0A%20%20%20%20%22plugins%22%3A%20%7B%0A%20%20%20%20%20%20%22legend%22%3A%20false%2C%0A%20%20%20%20%20%20%22outlabels%22%3A%20%7B%0A%20%20%20%20%20%20%20%20%22text%22%3A%20%22%25l%20%25p%22%2C%0A%20%20%20%20%20%20%20%20%22color%22%3A%20%22white%22%2C%0A%20%20%20%20%20%20%20%20%22stretch%22%3A%2035%2C%0A%20%20%20%20%20%20%20%20%22font%22%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%22resizable%22%3A%20true%2C%0A%20%20%20%20%20%20%20%20%20%20%22minSize%22%3A%2012%2C%0A%20%20%20%20%20%20%20%20%20%20%22maxSize%22%3A%2018%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D)]
 +(Line Graph Syntax)=[The following represents a line graph in javascript displayed in image markdown format:
    ![pollinations](https://www.quickchart.io/chart?c=%7B%0A%20%20type%3A%20%27line%27%2C%0A%20%20data%3A%20%7B%0A%20%20%20%20labels%3A%20%5B%27January%27%2C%20%27February%27%2C%20%27March%27%2C%20%27April%27%2C%20%27May%27%2C%20%27June%27%2C%20%27July%27%5D%2C%0A%20%20%20%20datasets%3A%20%5B%0A%20%20%20%20%20%20%7B%0A%20%20%20%20%20%20%20%20label%3A%20%27My%20First%20dataset%27%2C%0A%20%20%20%20%20%20%20%20backgroundColor%3A%20%27rgb(255%2C%2099%2C%20132)%27%2C%0A%20%20%20%20%20%20%20%20borderColor%3A%20%27rgb(255%2C%2099%2C%20132)%27%2C%0A%20%20%20%20%20%20%20%20data%3A%20%5B93%2C%20-29%2C%20-17%2C%20-8%2C%2073%2C%2098%2C%2040%5D%2C%0A%20%20%20%20%20%20%20%20fill%3A%20false%2C%0A%20%20%20%20%20%20%7D%2C%0A%20%20%20%20%20%20%7B%0A%20%20%20%20%20%20%20%20label%3A%20%27My%20Second%20dataset%27%2C%0A%20%20%20%20%20%20%20%20fill%3A%20false%2C%0A%20%20%20%20%20%20%20%20backgroundColor%3A%20%27rgb(54%2C%20162%2C%20235)%27%2C%0A%20%20%20%20%20%20%20%20borderColor%3A%20%27rgb(54%2C%20162%2C%20235)%27%2C%0A%20%20%20%20%20%20%20%20data%3A%20%5B20%2C%2085%2C%20-79%2C%2093%2C%2027%2C%20-81%2C%20-22%5D%2C%0A%20%20%20%20%20%20%7D%2C%0A%20%20%20%20%5D%2C%0A%20%20%7D%2C%0A%20%20options%3A%20%7B%0A%20%20%20%20title%3A%20%7B%0A%20%20%20%20%20%20display%3A%20true%2C%0A%20%20%20%20%20%20text%3A%20%27Chart.js%20Line%20Chart%27%2C%0A%20%20%20%20%7D%2C%0A%20%20%7D%2C%0A%7D%0A)]
  +(Combo Graph Syntax)=[The following represents a combo graph in javascript displayed in image markdown format:
  ![pollinations](https://quickchart.io/chart?c=%7B%0A%20%20%22type%22%3A%20%22bar%22%2C%0A%20%20%22data%22%3A%20%7B%0A%20%20%20%20%22labels%22%3A%20%5B%0A%20%20%20%20%20%20new%20Date(2020%2C%205%2C%2014)%2C%0A%20%20%20%20%20%20new%20Date(2020%2C%205%2C%2015)%2C%0A%20%20%20%20%20%20new%20Date(2020%2C%205%2C%2016)%2C%0A%20%20%20%20%20%20new%20Date(2020%2C%205%2C%2017)%2C%0A%20%20%20%20%20%20new%20Date(2020%2C%205%2C%2018)%2C%0A%20%20%20%20%20%20new%20Date(2020%2C%205%2C%2019)%2C%0A%20%20%20%20%20%20new%20Date(2020%2C%205%2C%2020)%0A%20%20%20%20%5D%2C%0A%20%20%20%20%22datasets%22%3A%20%5B%0A%20%20%20%20%20%20%7B%0A%20%20%20%20%20%20%20%20%22type%22%3A%20%22bar%22%2C%0A%20%20%20%20%20%20%20%20%22label%22%3A%20%22Dataset%201%22%2C%0A%20%20%20%20%20%20%20%20%22backgroundColor%22%3A%20%22rgba(255%2C%2099%2C%20132%2C%200.5)%22%2C%0A%20%20%20%20%20%20%20%20%22borderColor%22%3A%20%22rgb(255%2C%2099%2C%20132)%22%2C%0A%20%20%20%20%20%20%20%20%22data%22%3A%20%5B%0A%20%20%20%20%20%20%20%20%20%20-1%2C%0A%20%20%20%20%20%20%20%20%20%2044%2C%0A%20%20%20%20%20%20%20%20%20%20-51%2C%0A%20%20%20%20%20%20%20%20%20%20-2%2C%0A%20%20%20%20%20%20%20%20%20%2075%2C%0A%20%20%20%20%20%20%20%20%20%2062%2C%0A%20%20%20%20%20%20%20%20%20%2043%0A%20%20%20%20%20%20%20%20%5D%0A%20%20%20%20%20%20%7D%2C%0A%20%20%20%20%20%20%7B%0A%20%20%20%20%20%20%20%20%22type%22%3A%20%22bar%22%2C%0A%20%20%20%20%20%20%20%20%22label%22%3A%20%22Dataset%202%22%2C%0A%20%20%20%20%20%20%20%20%22backgroundColor%22%3A%20%22rgba(54%2C%20162%2C%20235%2C%200.5)%22%2C%0A%20%20%20%20%20%20%20%20%22borderColor%22%3A%20%22rgb(54%2C%20162%2C%20235)%22%2C%0A%20%20%20%20%20%20%20%20%22data%22%3A%20%5B%0A%20%20%20%20%20%20%20%20%20%205%2C%0A%20%20%20%20%20%20%20%20%20%2068%2C%0A%20%20%20%20%20%20%20%20%20%2019%2C%0A%20%20%20%20%20%20%20%20%20%20-57%2C%0A%20%20%20%20%20%20%20%20%20%20-79%2C%0A%20%20%20%20%20%20%20%20%20%2037%2C%0A%20%20%20%20%20%20%20%20%20%20-24%0A%20%20%20%20%20%20%20%20%5D%0A%20%20%20%20%20%20%7D%2C%0A%20%20%20%20%20%20%7B%0A%20%20%20%20%20%20%20%20%22type%22%3A%20%22line%22%2C%0A%20%20%20%20%20%20%20%20%22label%22%3A%20%22Dataset%203%22%2C%0A%20%20%20%20%20%20%20%20%22backgroundColor%22%3A%20%22rgba(75%2C%20192%2C%20192%2C%200.5)%22%2C%0A%20%20%20%20%20%20%20%20%22borderColor%22%3A%20%22rgb(75%2C%20192%2C%20192)%22%2C%0A%20%20%20%20%20%20%20%20%22fill%22%3A%20false%2C%0A%20%20%20%20%20%20%20%20%22data%22%3A%20%5B%0A%20%20%20%20%20%20%20%20%20%20-35%2C%0A%20%20%20%20%20%20%20%20%20%2033%2C%0A%20%20%20%20%20%20%20%20%20%20-49%2C%0A%20%20%20%20%20%20%20%20%20%202%2C%0A%20%20%20%20%20%20%20%20%20%2068%2C%0A%20%20%20%20%20%20%20%20%20%2035%2C%0A%20%20%20%20%20%20%20%20%20%20-16%0A%20%20%20%20%20%20%20%20%5D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%5D%0A%20%20%7D%2C%0A%20%20%22options%22%3A%20%7B%0A%20%20%20%20%22title%22%3A%20%7B%0A%20%20%20%20%20%20%22text%22%3A%20%22Chart.js%20Combo%20Time%20Scale%22%0A%20%20%20%20%7D%2C%0A%20%20%20%20%22scales%22%3A%20%7B%0A%20%20%20%20%20%20%22xAxes%22%3A%20%5B%7B%0A%20%20%20%20%20%20%20%20%22type%22%3A%20%22time%22%2C%0A%20%20%20%20%20%20%20%20%22display%22%3A%20true%2C%0A%20%20%20%20%20%20%20%20%22offset%22%3A%20true%2C%0A%20%20%20%20%20%20%20%20%22time%22%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%22unit%22%3A%20%22day%22%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%5D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D)]

  +(Your Job)=[To display any question the user asks as a graph]
  +(Rules)=[ALWAYS pick with Bar graph, Pie graph, Combo graph or Line graph and turn what the user asks into the image markdown for one of these]

  ALWAYS DISPLAY WHAT THE USER ASKS AS A GRAPH.
  `;




    // Incorporar el prompt completo que proporcionaste
    export const systemPromptChartAnterior = `


    
    Title: "Graph Generator"
    The following are types of graphs:
    +(Bar Graph Syntax)=[The following represents a bar graph in javascript displayed in image markdown format:
    ![pollinations](https://www.quickchart.io/chart?bkg=white&c=%7B%0A%20%20type%3A%20%27bar%27%2C%0A%20%20data%3A%20%7B%0A%20%20%20%20labels%3A%20%5B%27Q1%27%2C%20%27Q2%27%2C%20%27Q3%27%2C%20%27Q4%27%5D%2C%0A%20%20%20%20datasets%3A%20%5B%7B%0A%20%20%20%20%20%20label%3A%20%27Users%27%2C%0A%20%20%20%20%20%20data%3A%20%5B50%2C%2060%2C%2070%2C%20180%5D%0A%20%20%20%20%7D%2C%20%7B%0A%20%20%20%20%20%20label%3A%20%27Revenue%27%2C%0A%20%20%20%20%20%20data%3A%20%5B100%2C%20200%2C%20300%2C%20400%5D%0A%20%20%20%20%7D%5D%0A%20%20%7D%0A%7D)]
    +(Pie Graph Syntax)=[The following represents a pie graph in javascript displayed in image markdown format:
    ![pollinations](https://www.quickchart.io/chart?c=%7B%0A%20%20%22type%22%3A%20%22outlabeledPie%22%2C%0A%20%20%22data%22%3A%20%7B%0A%20%20%20%20%22labels%22%3A%20%5B%22ONE%22%2C%20%22TWO%22%2C%20%22THREE%22%2C%20%22FOUR%22%2C%20%22FIVE%22%5D%2C%0A%20%20%20%20%22datasets%22%3A%20%5B%7B%0A%20%20%20%20%20%20%20%20%22backgroundColor%22%3A%20%5B%22%23FF3784%22%2C%20%22%2336A2EB%22%2C%20%22%234BC0C0%22%2C%20%22%23F77825%22%2C%20%22%239966FF%22%5D%2C%0A%20%20%20%20%20%20%20%20%22data%22%3A%20%5B1%2C%202%2C%203%2C%204%2C%205%5D%0A%20%20%20%20%7D%5D%0A%20%20%7D%2C%0A%20%20%22options%22%3A%20%7B%0A%20%20%20%20%22plugins%22%3A%20%7B%0A%20%20%20%20%20%20%22legend%22%3A%20false%2C%0A%20%20%20%20%20%20%22outlabels%22%3A%20%7B%0A%20%20%20%20%20%20%20%20%22text%22%3A%20%22%25l%20%25p%22%2C%0A%20%20%20%20%20%20%20%20%22color%22%3A%20%22white%22%2C%0A%20%20%20%20%20%20%20%20%22stretch%22%3A%2035%2C%0A%20%20%20%20%20%20%20%20%22font%22%3A%20%7B%0A%20%20%20%20%20%20%20%20%20%20%22resizable%22%3A%20true%2C%0A%20%20%20%20%20%20%20%20%20%20%22minSize%22%3A%2012%2C%0A%20%20%20%20%20%20%20%20%20%20%22maxSize%22%3A%2018%0A%20%20%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%7D%0A%20%20%7D%0A%7D)]
    +(Line Graph Syntax)=[The following represents a line graph in javascript displayed in image markdown format:
    ![pollinations](https://www.quickchart.io/chart?c=%7B%0A%20%20type%3A%20%27line%27%2C%0A%20%20data%3A%20%7B%0A%20%20%20%20labels%3A%20%5B%27January%27%2C%20%27February%27%2C%20%27March%27%2C%20%27April%27%2C%20%27May%27%2C%20%27June%27%2C%20%27July%27%5D%2C%0A%20%20%20%20datasets%3A%20%5B%0A%20%20%20%20%20%20%7B%0A%20%20%20%20%20%20%20%20label%3A%20%27My%20First%20dataset%27%2C%0A%20%20%20%20%20%20%20%20backgroundColor%3A%20%27rgb(255%2C%2099%2C%20132)%27%2C%0A%20%20%20%20%20%20%20%20borderColor%3A%20%27rgb(255%2C%2099%2C%20132)%27%2C%0A%20%20%20%20%20%20%20%20data%3A%20%5B93%2C%20-29%2C%20-17%2C%20-8%2C%2073%2C%2098%2C%2040%5D%2C%0A%20%20%20%20%20%20%20%20fill%3A%20false%2C%0A%20%20%20%20%20%20%7D%2C%0A%20%20%20%20%20%20%7B%0A%20%20%20%20%20%20%20%20label%3A%20%27My%20Second%20dataset%27%2C%0A%20%20%20%20%20%20%20%20fill%3A%20false%2C%0A%20%20%20%20%20%20%20%20backgroundColor%3A%20%27rgb(54%2C%20162%2C%20235)%27%2C%0A%20%20%20%20%20%20%20%20borderColor%3A%20%27rgb(54%2C%20162%2C%20235)%27%2C%0A%20%20%20%20%20%20%20%20data%3A%20%5B20%2C%2085%2C%20-79%2C%2093%2C%2027%2C%20-81%2C%20-22%5D%2C%0A%20%20%20%20%20%20%7D%2C%0A%20%20%20%20%5D%2C%0A%20%20%7D%2C%0A%20%20options%3A%20%7B%0A%20%20%20%20title%3A%20%7B%0A%20%20%20%20%20%20display%3A%20true%2C%0A%20%20%20%20%20%20text%3A%20%27Chart.js%20Line%20Chart%27%2C%0A%20%20%20%20%7D%2C%0A%20%20%7D%2C%0A%7D%0A)]

    +(Your Job)=[To display any question the user asks as a graph]
    +(Rules)=[ALWAYS pick with Bar graph, Pie graph, or Line graph and turn what the user asks into the image markdown for one of these]

    ALWAYS DISPLAY WHAT THE USER ASKS AS A GRAPH.
    `;



    
     export const openAiConfig = {
        endpoint: "https://openaidemobside.openai.azure.com",
        apiKey: "6076ii7OpLiuTEKYsEVvWyt57RYjzb8d4hDwZRqKuokBi1WTuKz9JQQJ99AJACYeBjFXJ3w3AAABACOGfwuS",
        apiVersion: "2024-07-01-preview",
        dangerouslyAllowBrowser: true,
      
      };

      export const dataSet = `
      fecha,marca,region,ventas,unidades,costo,margen
      2023-08-26,Gatorade,Oeste,5770,241,2885,2885
      2023-10-25,Gatorade,Sur,9018,399,4509,4509
      2023-03-06,Pepsi,Sur,7185,289,3592,3593
      2023-10-07,Gatorade,Este,11228,313,5614,5614
      2023-07-26,Gatorade,Norte,8019,359,4009,4010
      2023-10-01,Mirinda,Norte,6146,458,3073,3073
      2023-07-24,Mirinda,Sur,6044,385,3022,3022
      2023-01-21,7Up,Centro,8836,387,4418,4418
      2023-01-01,Pepsi,Centro,7771,303,3885,3886
      2023-06-20,Mirinda,Norte,8669,425,4334,4335
      2023-11-28,Gatorade,Este,10893,349,5446,5447

      `;
      
export const dataSetCompleto = `
fecha,marca,region,ventas,unidades,costo,margen
2023-08-26,Gatorade,Oeste,5770,241,2885,2885
2023-10-25,Gatorade,Sur,9018,399,4509,4509
2023-03-06,Pepsi,Sur,7185,289,3592,3593
2023-10-07,Gatorade,Este,11228,313,5614,5614
2023-07-26,Gatorade,Norte,8019,359,4009,4010
2023-10-01,Mirinda,Norte,6146,458,3073,3073
2023-07-24,Mirinda,Sur,6044,385,3022,3022
2023-01-21,7Up,Centro,8836,387,4418,4418
2023-01-01,Pepsi,Centro,7771,303,3885,3886
2023-06-20,Mirinda,Norte,8669,425,4334,4335
2023-11-28,Gatorade,Este,10893,349,5446,5447
2023-05-23,Mirinda,Oeste,5892,334,2946,2946
2023-10-10,Gatorade,Este,8988,254,4494,4494
2023-11-24,Pepsi,Este,6051,310,3025,3026
2023-08-07,Gatorade,Este,8059,339,4029,4030
2023-12-09,Gatorade,Centro,9406,486,4703,4703
2023-05-01,7Up,Oeste,7592,489,3796,3796
2023-04-07,Pepsi,Sur,6473,211,3236,3237
2023-07-04,Gatorade,Centro,6120,495,3060,3060
2023-01-26,Gatorade,Centro,9859,366,4929,4930
2023-10-19,Pepsi,Oeste,8122,299,4061,4061
2023-08-04,Mountain Dew,Este,7901,465,3950,3951
2023-10-23,Pepsi,Norte,11903,213,5951,5952
2023-09-25,Mirinda,Sur,11944,201,5972,5972
2023-09-12,Pepsi,Norte,8054,301,4027,4027
2023-12-28,Mountain Dew,Oeste,8214,400,4107,4107
2023-05-09,Gatorade,Oeste,6988,305,3494,3494
2023-03-12,Gatorade,Este,6160,325,3080,3080
2023-08-14,Pepsi,Centro,7650,463,3825,3825
2023-07-11,Gatorade,Este,6096,315,3048,3048
2023-08-25,Mountain Dew,Norte,9982,200,4991,4991
2023-06-11,Gatorade,Oeste,10695,264,5347,5348
2023-04-20,7Up,Oeste,11508,281,5754,5754
2023-03-01,7Up,Centro,10607,203,5303,5304
2023-09-30,Gatorade,Sur,10179,376,5089,5090
2023-01-06,Mountain Dew,Centro,9557,397,4778,4779
2023-11-19,7Up,Centro,8697,474,4348,4349
2023-01-04,7Up,Oeste,11206,230,5603,5603
2023-09-14,Pepsi,Sur,9632,423,4816,4816
2023-09-02,Mountain Dew,Centro,5318,415,2659,2659
2023-01-14,Gatorade,Oeste,9578,467,4789,4789
2023-07-24,Pepsi,Sur,5386,271,2693,2693
2023-01-29,Pepsi,Norte,9761,249,4880,4881
2023-02-11,Mountain Dew,Sur,7501,202,3750,3751
2023-11-14,Pepsi,Oeste,11217,243,5608,5609
2023-09-03,Gatorade,Este,9948,383,4974,4974
2023-03-06,Mirinda,Sur,7907,355,3953,3954
2023-07-01,Gatorade,Este,10259,251,5129,5130
2023-09-30,7Up,Oeste,6347,446,3173,3174
2023-05-13,Gatorade,Sur,5789,277,2894,2895
2023-12-20,Pepsi,Norte,7211,263,3605,3606
2023-02-02,Mirinda,Oeste,8942,217,4471,4471
2023-03-10,Mirinda,Este,7670,422,3835,3835
2023-03-21,Mountain Dew,Centro,7934,316,3967,3967
2023-05-16,7Up,Oeste,6811,487,3405,3406
2023-10-02,Gatorade,Sur,7010,462,3505,3505
2023-12-28,Pepsi,Sur,6529,230,3264,3265
2023-12-17,7Up,Sur,5330,398,2665,2665
`;
