# Outlook2Aula (O2A)
Et forsøg på at lave et simpelt grafisk program, som kan overføre begivenheder fra Outlook til Aula "automatisk". Det er tale om en en-vejsoverførsel.
Dette er en grafisk overflade til det oprindelige "[O2A script](https://github.com/froksen/O2A)" udviklet til samme formål.


![alt text](https://github.com/froksen/O2A_GUI/blob/master/screenshot.PNG?raw=true)



## Hvordan virker det (Forsimplet)
Når en begivenhed oprettes i Outlook, da kan man tilføje kategorien "AULA" til begivenheden. Når så Outlook2Aula afvikles, da vil alle begivenheder markeret med denne kategori overføres til AULA.

## Hvad virker?
- At oprette heldags- eller tidsafgrænsede begivenheder til AULA fra Outlook
- At opdatere heldags- eller tidsafgrænsede begivenheder til AULA fra Outlook
- At slette heldags- eller tidsafgrænsede begivenheder til AULA fra Outlook
- At tilføje deltagere fra Outlook begivenheden til AULA begivenheden, hvis de findes indenfor samme institution som en selv.

## Hvad virker ikke - helt endnu?
- Gentagende begivenheder
- Overføre vedhæftede filer/medier fra Outlook til AULA
- At overføre deadlines, påmindelser m.v. fra Outlook til AULA.

## Tekniske krav
* Python 3, se "Requirements.txt" for afhængigheder
* (Anbefales) Git, bruges til at holde programmet opdateret

## Afvikling

### Fælles for tilgangene
* Installer de tekniske krav
* Hent seneste udgave her fra Github

### Med git installeret 
1. Åben mappen "O2A" i Stifinder
2. Kør batch-filen kaldet "updateandrun.bat". Denne fil opdaterer (via Git) og installerer (Via Pip) afhængighederne for programmet, samt starter det grafiske program.

### Uden git installeret
1. Åben mappen "O2A" i Stifinder
2. Installer afhængighederne for programmet ved at køre "pip install -r Requirements.txt"
3. Derefter start programmet enten ved at dobbeltklippe på "main.pyw" eller køre "python main.pyw".

