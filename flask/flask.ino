// Bibliotecas
#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

// Pinos
#define DHTPIN 13        // Pino conectado ao DHT11 (4, neste caso)
#define DHTTYPE DHT11   // Tipo do sensor DHT



// Assuming you're using HTTP server or MQTT to receive data
int led1Pin = 25;
int led2Pin = 26;
int led3Pin = 27;

void setup() {
  pinMode(led1Pin, OUTPUT);
  pinMode(led2Pin, OUTPUT);
  pinMode(led3Pin, OUTPUT);
  // Setup WiFi and server or MQTT here
}

DHT dht(DHTPIN, DHTTYPE);

// Credenciais WiFi
const char* ssid = "id"; 
const char* password = "senha" ;

// URL do servidor Flask
const char* serverName = "ip"; // Alterar para o IP do seu servidor Flask

void setup() {
  Serial.begin(115200);
  
  // Conectando ao WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Conectando ao WiFi...");
  }
  Serial.println("Conectado ao WiFi.");

  dht.begin();
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    // Fazendo leitura dos dados
    float temperatura = dht.readTemperature();
    float umidade = dht.readHumidity();

    if (isnan(temperatura) || isnan(umidade)) {
      Serial.println("Falha ao ler o sensor DHT!");
    } else {
      // Prepara os dados em formato JSON
      String jsonData = "{\"temperatura\":" + String(temperatura) + ",\"umidade\":" + String(umidade) + "}";
      
      // Envia os dados para o servidor Flask
      http.begin(serverName);
      http.addHeader("Content-Type", "application/json");
      int httpResponseCode = http.POST(jsonData);
      
      // Verifica a resposta do servidor
      if (httpResponseCode > 0) {
        String response = http.getString();
        Serial.println(httpResponseCode);
        Serial.println(response);
      } else {
        Serial.print("Erro no envio de dados. Código: ");
        Serial.println(httpResponseCode);
      }
      
      http.end();
    }
  } else {
    Serial.println("Conexão WiFi perdida.");
  }

  // Aguarda 10 segundos antes de enviar novos dados
  delay(10000);
}

void setPWMLed(int ledPin, int value) {
  int pwmValue = map(value, 0, 100, 0, 255);
  analogWrite(ledPin, pwmValue);
}