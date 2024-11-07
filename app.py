from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string(open("index.html").read())

@app.route('/consultar', methods=['POST'])
def consultar():
    fecha = request.form.get('fecha')
    liga = request.form.get('liga')
    casas_de_apuestas = ["bet365", "codere", "williamhill", "bwin", "sportium", "888sport", "marathonbet", "betsson"]
    logos_casas = {
        "bet365": "/images/casas/mini/mini_bet365.png",
        "codere": "/images/casas/mini/mini_codere.png",
        "williamhill": "/images/casas/mini/mini_williamhill.png",
        "bwin": "/images/casas/mini/mini_bwin.png",
        "sportium": "/images/casas/mini/mini_sportium.png",
        "888sport": "/images/casas/mini/mini_888sport.png",
        "marathonbet": "/images/casas/mini/mini_marathonbet.png",
        "betsson": "/img/betsson.jpeg"
    }
    # URL para thepunterspage (porcentjs)
    if liga == "premier-league":
        url_punters = f"https://www.thepunterspage.com/kickform/premier-league-matchday-tips/{fecha}/"
    elif liga == "la-liga":
        url_punters = f"https://www.thepunterspage.com/kickform/la-liga-matchday-tips/{fecha}/"
    else:
        return "Liga no soportada."

    # URL para elcomparador (mejor casa de apuestas)
    if liga == "premier-league":
        url_comparador = f"http://www.elcomparador.com/futbol/inglaterra/premierleague/jornada{fecha}"
    elif liga == "la-liga":
        url_comparador = f"http://www.elcomparador.com/futbol/españa/primeradivision/jornada{fecha}"
    

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    team_data = []

    try:
        response_punters = requests.get(url_punters, headers=headers)
        soup_punters = BeautifulSoup(response_punters.content, "html.parser")
        match_cards = soup_punters.find_all("div", class_="card_new")

        for match in match_cards:
            team_home = match.find("div", class_="team home").find("span", class_="teamname").get_text(strip=True)
            team_away = match.find("div", class_="team away").find("span", class_="teamname").get_text(strip=True)
            
            # Probabilidades
            prob_elements = match.find("div", class_="predict")
            if prob_elements:
                prob_home = prob_elements.find("div", class_="first").find("div", class_="prozent").get_text(strip=True) if prob_elements.find("div", class_="first") else "No disponible"
                prob_draw = prob_elements.find("div", class_="second").find("div", class_="prozent").get_text(strip=True) if prob_elements.find("div", class_="second") else "No disponible"
                prob_away = prob_elements.find("div", class_="third").find("div", class_="prozent").get_text(strip=True) if prob_elements.find("div", class_="third") else "No disponible"
            else:
                prob_home, prob_draw, prob_away = "No disponible", "No disponible", "No disponible"

            # agrega al equipo los datos de probabilidades e inicializa las cuotas de El Comparador
            team_data.append({
                "team_home": team_home,
                "prob_home": prob_home,
                "prob_draw": prob_draw,
                "team_away": team_away,
                "prob_away": prob_away,
                "max_home": None,
                "max_draw": None,
                "max_away": None,
                "min_of_max_odds": "No disponible" 
            })

    except Exception as e:
        return f"Error en thepunterspage: {e}"


    try:
        response_comparador = requests.get(url_comparador, headers=headers)
        soup_comparador = BeautifulSoup(response_comparador.content, "html.parser")
        matches = soup_comparador.find_all("div", id="contenedor_evento")

        for match in matches:
            # agarra los nombres de los equipos desde el HTML de elcomparador
            team_elements = match.find_all("span", class_="equipo")
            if len(team_elements) < 2:
                continue  

            team_1 = team_elements[0].get_text(strip=True)
            team_2 = team_elements[1].get_text(strip=True)

            odds = {
                "home": [],
                "draw": [],
                "away": []
            }
            houses = {
                "home": [],
                "draw": [],
                "away": []
            }

            # extrae cuotas y casas de apuestas basadas en la posición del coso
            rows = match.find("div", id="contenedor_cuotas").find_all("div", id="fila_cuotas")
            for row in rows:
                outcome = row.find("div", class_="apuesta").get_text(strip=True)
                odds_values = row.find_all("div", class_="impar") + row.find_all("div", class_="par")

                # asigna la casa de apuestas en función de la posición en la fila
                for index, odd in enumerate(odds_values):
                    link = odd.find("a")
                    if link and index < len(casas_de_apuestas):
                        value = float(odd.get_text(strip=True))
                        house = casas_de_apuestas[index]  
                        if outcome == "1":
                            odds["home"].append(value)
                            houses["home"].append(house)
                        elif outcome == "X":
                            odds["draw"].append(value)
                            houses["draw"].append(house)
                        elif outcome == "2":
                            odds["away"].append(value)
                            houses["away"].append(house)

            # verifica equipos en team_data y asigna la cuota mínima y su casa de apuestas
            for item in team_data:
                team_home = item["team_home"]
                team_away = item["team_away"]

                # Ajustes para nombres si cambian entre pagina y pagina
                if team_home == "Tottenham Hotspur":
                    team_home = "Tottenham"
                elif team_home == "Ipswich Town":
                    team_home = "Ipswich"
                elif team_home == "West Ham United":
                    team_home = "West Ham"
                elif team_home == "AFC Bournemouth":
                    team_home = "Bournemouth"
                elif team_home == "Brighton":
                    team_home = "Brighton"
                elif team_home == "Newcastle United":
                    team_home = "Newcastle"
                elif team_home == "Leicester City":
                    team_home = "Leicester"

                if team_away == "Tottenham Hotspur":
                    team_away = "Tottenham"
                elif team_away == "Ipswich Town":
                    team_away = "Ipswich"
                elif team_home == "West Ham United":
                    team_home = "West Ham"
                elif team_home == "AFC Bournemouth":
                    team_home = "Bournemouth"
                elif team_home == "Brighton":
                    team_home = "Brighton"
                elif team_home == "Newcastle United":
                    team_home = "Newcastle"
                elif team_home == "Leicester City":
                    team_home = "Leicester"

                if team_1.lower() in (team_home.lower(), team_away.lower()) or \
                team_2.lower() in (team_home.lower(), team_away.lower()):

                    # calcula las cuotas maximas y las casas de apuestas asociadas
                    max_home = max(odds["home"], default=float('inf'))
                    max_draw = max(odds["draw"], default=float('inf'))
                    max_away = max(odds["away"], default=float('inf'))

                    # agarra la cuota más baja entre las máximas 
                    min_of_max_odds = min(max_home, max_draw, max_away)
                    if min_of_max_odds == max_home:
                        house = houses["home"][odds["home"].index(max_home)]
                    elif min_of_max_odds == max_draw:
                        house = houses["draw"][odds["draw"].index(max_draw)]
                    else:
                        house = houses["away"][odds["away"].index(max_away)]

                    # agarra la URL del logo de la casa de apuestas
                    house_logo = logos_casas.get(house, "")

                    # Guardar cuota y logo de la casa de apuestas en el item
                    item["min_of_max_odds"] = f"{min_of_max_odds} <img src='{house_logo}' alt='{house}' style='width: 20px; height: 20px;' />" if min_of_max_odds != float('inf') else "No disponible"
                    break  

    except Exception as e:
        return f"Error en elcomparador: {e}"

    # creacion de la tabla HTML con solo la cuota mínima de las máximas y el logo de la casa de apuestas
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Probabilidades y Cuotas - Fecha {fecha}</title>
        <style>
            body {{ background-color: #121212; color: #e0e0e0; font-family: Arial, sans-serif; }}
            table {{ width: 90%; margin: 20px auto; border-collapse: collapse; }}
            th, td {{ padding: 10px; border: 1px solid #333; text-align: center; }}
            th {{ background-color: #212121; color: #39ff14; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #1b1b1b; }}
            tr:hover {{ background-color: #333333; color: #39ff14; transition: background-color 0.3s ease; }}

            #neon-background {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: -1;
                background-color: #121212;
            }}
        </style>
    </head>
    <body>
        <canvas id="neon-background"></canvas>
        <h1 style="text-align:center; color:#39ff14;">Probabilidades y Cuotas - Fecha {fecha}</h1>
        <table>
            <tr>
                <th>Equipo Local</th>
                <th>Probabilidad Local</th>
                <th>Probabilidad Empate</th>
                <th>Equipo Visitante</th>
                <th>Probabilidad Visitante</th>
                <th>Mejor Cuota</th>
            </tr>
    """

    for item in team_data:
        html_content += f"""
            <tr>
                <td>{item['team_home']}</td>
                <td>{item['prob_home']}</td>
                <td>{item['prob_draw']}</td>
                <td>{item['team_away']}</td>
                <td>{item['prob_away']}</td>
                <td>{item['min_of_max_odds']}</td>
            </tr>
        """

    html_content += """

        </table>
        <script>
        document.addEventListener("DOMContentLoaded", () => {
            const canvas = document.getElementById("neon-background");
            const ctx = canvas.getContext("2d");
        
            let particlesArray = [];
            const colors = ["#39ff14", "#00e5ff", "#ff0", "#f0f"]; // Colores neón para las partículas
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        
            // Ajustar el tamaño del canvas al cambiar el tamaño de la ventana
            window.addEventListener("resize", () => {
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
            });
        
            // Crear partículas
            class Particle {
                constructor() {
                    this.x = Math.random() * canvas.width;
                    this.y = Math.random() * canvas.height;
                    this.size = Math.random() * 3 + 1; // Tamaño de la partícula
                    this.color = colors[Math.floor(Math.random() * colors.length)];
                    this.speedX = Math.random() * 2 - 1; // Velocidad en el eje X
                    this.speedY = Math.random() * 2 - 1; // Velocidad en el eje Y
                }
                update() {
                    this.x += this.speedX;
                    this.y += this.speedY;
                    if (this.size > 0.2) this.size -= 0.02; // Reducir el tamaño para dar efecto de desvanecimiento
                }
                draw() {
                    ctx.beginPath();
                    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                    ctx.fillStyle = this.color;
                    ctx.shadowBlur = 8;
                    ctx.shadowColor = this.color;
                    ctx.fill();
                }
            }
        
            // Crear un número inicial de partículas
            function initParticles() {
                particlesArray = [];
                for (let i = 0; i < 100; i++) {
                    particlesArray.push(new Particle());
                }
            }
        
            // Animación de las partículas
            function animateParticles() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                for (let i = 0; i < particlesArray.length; i++) {
                    particlesArray[i].update();
                    particlesArray[i].draw();
        
                    // Reemplazar la partícula si se vuelve demasiado pequeña
                    if (particlesArray[i].size <= 0.2) {
                        particlesArray.splice(i, 1);
                        particlesArray.push(new Particle());
                    }
                }
                requestAnimationFrame(animateParticles);
            }
        
            // Inicializar y animar
            initParticles();
            animateParticles();
        });
    </script></body></html>
    """
    return html_content


if __name__ == '__main__':
    app.run(debug=True)
