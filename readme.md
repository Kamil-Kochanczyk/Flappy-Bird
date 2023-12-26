# Flappy Bird (pygame)

## Wprowadzenie

Flappy Bird to popularna gra typu *side-scrolling*, w której gracz wciela się w postać lecącego ptaka, którym musi omijać rury wystające z góry i z dołu ekranu. Jeżeli gracz przeleci ptakiem przez szparę między wystającymi rurami, to dostaje jeden punkt. Celem gry jest zdobycie jak największej liczby punktów. Gra się kończy, jeżeli ptak uderzy w jakąś rurę, albo jeżeli spadnie na ziemię.

W grze tej nie ma maksymalnej liczby punktów do zdobycia - nieważne ile punktów się zdobędzie, zawsze można pobić swój rekord i zdobyć przynajmniej jeden punkt więcej.

W tej implementacji gry wprowadzono dodatkowe utrudnienia dla gracza. Na przykład, rury nie zawsze są statyczne - mogą poruszać się w górę i w dół. Ponadto, ptak nie może uderzyć w sufit (czyli w górną krawędź ekranu), a jeżeli uderzy - gra się kończy.

## Interfejs

Gracz rozpoczyna grę i steruje ptakiem za pomocą spacji.

Gracz może wyłączyć grę w dowolnym momencie poprzez naciśnięcie klawisza "q".

Jeżeli gra się skończy, ale gracz uzyska satysfakcjonujący wynik, to może go zapisać naciskając klawisz "s". Po naciśnięciu klawisza pojawi się okienko z prośbą do gracza o podanie swojego identyfikatora. Po podaniu identyfikatora wynik zostanie zapisany do pliku *leaderboard.json*.

Informacje zapisywane do pliku obejmują:

- identyfikator gracza
- dokładną datę i godzinę, w której gracz uzyskał dany wynik
- wynik uzyskany przez gracza

W pliku *leaderboard.json* będą znajdowały się wszystkie wyniki zapisane przez gracza. Gracz może zobaczyć zawartość tego pliku w dowolnym momencie gry, wystarczy że naciśnie klawisz "p". Zawartość pliku zostanie wtedy wypisana w konsoli.

## Implementacja

W tym rozdziale zostanie wyjaśniony ogólny pomysł na wykonanie programu. Nie zostanie omówiony cały kod programu - omówione zostaną tylko te fragmenty, które dla autora wydają się najważniejsze.

### Ogólne uwagi

- Ptak wcale nie porusza się w prawo, ptak porusza się tak naprawdę tylko w górę i w dół (w kierunku pionowym). To ziemia i rury poruszają się w lewo i sprawiają wrażenie, że to ptak porusza się w prawo.
- W grze nie ma klasy reprezentującej pojedynczą rurę. W grze jest klasa reprezentująca pojedynczą szparę między rurami. Szpara ta to tak jakby pusty prostokąt, przez który może przelecieć ptak. Ma on szerokość taką samą jak szerokość rury i jakąś tam wysokość. Względem tej szpary można określić rury tworzące tę szparę. Szpara wyznacza więc jednoznacznie tak jakby kolumnę, która składa się z trzech elementów: ze szpary, z rury powyżej szpary i z rury poniżej szpary.
- Kolumn pojawiających się przed ptakiem i przesuwających się w lewo przez ekran nie jest aż tak wiele. Są tak naprawdę tylko trzy. Poruszają się one cyklicznie, w kółko, przeskakują poza ekranem z lewej strony na prawą i sprawiają iluzję, że się pojawiają coraz to kolejne kolumny. Szczegóły poniżej.
- Do zapisywania wyników do pliku postanowiono użyć formatu JSON. Szczegóły poniżej.
- Zakłada się, że układ współrzędnych wyznacza lewy górny róg ekranu. Oś x jest skierowana w prawo, a oś y jest skierowana w dół.

### Ptak

Najważniejszą kwestią dotyczącą ptaka jest to jak został zaimplementowany jego ruch i kontrola.

Ruch ptaka to spadek swobodny pod wpływem siły grawitacji, albo też rzut pionowy. Ruch taki opisuje równanie $y(t)=y_{0}+v_{0}t+\frac{1}{2}gt^{2}$.

Równaniu temu odpowiada w kodzie funkcja `y(t, y0, v0)`.

```python
def y(t, y0, v0):
    """Returns the current y position of the center of the bird."""
    return y0 + v0 * t + (1 / 2) * G * t * t
```

W grze są dwa przypadki ruchu opisanego powyższym równaniem.

Pierwszy przypadek jest wtedy, gdy $v_{0}<0$. Powyższe równanie opisuje wtedy ruch, gdzie prędkość początkowa jest skierowana w górę. W tym przypadku ciało najpierw porusza się do góry. W miarę upływu czasu grawitacja spowalnia ruch ciała do góry, aż w końcu ciało się zatrzymuje. Następnie grawitacja sprawia, że ciało zaczyna spadać w dół. Widać więc, że ten przypadek nadaje się do opisania i zaimplementowania podskoku ptaka.

Gdy gracz naciśnie po raz pierwszy spacje by rozpocząć grę, to mierzony jest czas $t_{0}$, w którym nastąpiło naciśnięcie spacji. Odpowiada on argumentowi $t=0$ w równaniu na $y(t)$. Dzięki temu, można potem w głównej pętli gry mierzyć upływ czasu, czyli wartość argumentu $t$, traktując $t_{0}$ jako punkt odniesienia. Przy naciśnięciu spacji odczytywana jest też wartość $y_{0}$, czyli pozycja ptaka w momencie naciśnięcia spacji. Wartość $v_{0}$ jest predefiniowaną stałą. Wartości $t$, $y_{0}$ i $v_{0}$ są przekazywane do funkcji `y(t, y0, v0)`, która zwraca pozycję pozycję ptaka w czasie zgodnie z równaniem na $y(t)$. Funkcja ta jest wywoływana także w kolejnych iteracjach głównej pętli gry, a jedyne co się zmienia to wartość $t$. Ostatecznie ptak porusza się więc zgodnie z pierwszym przypadkiem ruchu: najpierw w górę, potem w dół.

Do momentu gdy gracz nie naciśnie ponownie spacji, jedyna wartość jaka ulega zmianie to wartość czasu $t$. Gdy gracz naciśnie ponownie spację, wszystko dzieje się tak, jakby spacja była naciśnięta dopiero po raz pierwszy. Znów mierzony jest czas $t_{0}$ i względem tej nowej wartości $t_{0}$ mierzony jest od tego momentu czas $t$. Znowu odczytywana jest wartość $y_{0}$, czyli pozycja ptaka w momencie kolejnego naciśnięcia spacji. Wartość $v_{0}$ jest predefiniowaną stałą. Zaaktualizowane wartości przekazywane są do funkcji `y(t, y0, vo)` w kolejnych iteracjach głównej pętli gry. Ostatecznie ruch jest analogiczny jak poprzednio, ale inne są warunki początkowe, ponieważ inna jest wartość $y_{0}$.

Można powiedzieć, że każde naciśnięcie spacji odpowiada nowemu rzutowi pionowemu, który jest niezależny od pozostałych i jest opisywany równaniem na $y(t)$. Jednak każdy taki rzut pionowy zawsze jest analogiczny do pozostałych: najpierw ptak porusza się w górę, potem grawitacja go spowalnia i zatrzymuje, aż w końcu zaczyna ciągnąć go w dół. W każdym rzucie pionowym inne są tylko wartości $y_{0}$, a więc inne są warunki początkowe równania na $y(t)$.

```python
while True:
    (...)
            # Player pressed space - controlling the game
            if event.key == pygame.K_SPACE:
                (...)
                if game_state == GAME_RUNNING:
                    t0 = pygame.time.get_ticks()
                    y0 = bird.centery
                    v0 = V0
                (...)
    # What happens when the player has started playing
    if game_state == GAME_RUNNING:
        (...)
        # Calculate the current y position of the bird
        t = (pygame.time.get_ticks() - t0) / 1000.0
        bird.centery = y(t, y0, v0)
        (...)
```

Drugi przypadek jest wtedy, gdy $v_{0}=0$. Odpowiada to sytuacji, gdy ciało zaczyna od razu spadać swobodnie pod wpływem siły grawitacji, ponieważ nie ma żadnej prędkości początkowej. W grze sytuacja ta występuje tylko wtedy, gdy ptak w coś uderzy. Następuje wówczas koniec gry i ptak zaczyna spadać bezwładnie, aż nie uderzy w ziemię (naciskanie spacji wtedy nic nie robi). Logika jest taka sama jak w pierwszym przypadku, jedyna różnica jest taka, że tym razem $v_{0}=0$.

```python
while True:
    (...)
    # What happens when the player has started playing
    if game_state == GAME_RUNNING:
        (...)
        # Check if the player hit something...
        hit_pipe = bird.hits(top_pipe_ahead) or bird.hits(bottom_pipe_ahead)
        hit_floor = bird.bottom >= base_y
        hit_ceiling = bird.top <= 0

        # ... and if so, make the bird fall and end the current game
        if hit_pipe or hit_ceiling or hit_floor:
            t0 = pygame.time.get_ticks()
            y0 = bird.centery
            v0 = 0
            bird_falling = True
            (...)
            game_state = GAME_END
    (...)
    # What happens when the player has lost and the game is over
    if game_state == GAME_END:

        # Make the bird fall freely until it hits the ground
        if bird.bottom <= base_y:
            t = (pygame.time.get_ticks() - t0) / 1000.0
            bird.centery = y(t, y0, v0)
        else:
            bird_falling = False
        (...)
```

W grze przyjęto, że $v_{0}=-2.8$ (wartość znaleziono eksperymentalnie), i że wartość stałej grawitacji to $g=10$. Wektory trzeba było powiększyć, ponieważ były zbyt małe w układzie współrzędnych wyznaczonym przez ekran gry.

```python
(...)
# Constants controlling the mechanics of the game
SCALING_FACTOR = 220          # makes the length of vectors bigger
V0 = -2.8 * SCALING_FACTOR    # velocity/force making the bird jump upwards
G = 10 * SCALING_FACTOR       # gravity
(...)
```

### Rury

Jak już to zostało wcześniej wspomniane, nie ma klasy reprezentującej rurę, tylko jest klasa reprezentująca szparę między rurami. Szpara to tak naprawdę pusty prostokąt, który ma określoną pozycję i rozmiary i może się dodatkowo poruszać w górę lub w dół (ale nie musi). Szparę reprezentuje obiekt klasy `Gap`. Ponieważ rozmiary szpary są predefiniowane przez stałe, jedyne atrybuty jakie posiada obiekt klasy `Gap` to atrybuty określające pozycję i prędkość poruszania się w kierunku pionowym.

Szpara jednoznacznie wyznacza kolumnę złożoną ze szpary, rury powyżej szpary i rury poniżej szpary. Takie właśnie kolumny przesuwają się w lewo podczas gry i gracz musi tak sterować ptakiem, by przelatywać nim przez szpary i nie dotykać żadnej rury. Zbiór tych przesuwających się kolumn jest reprezentowany w programie przez obiekt klasy `MovingGaps`. Jednym z atrybutów obiektu `MovingGaps` jest więc naturalnie lista obiektów `Gap`.

Wydaje się, że skoro w grze bez przerwy pojawiają się nowe kolumny przed ptakiem, to lista zawarta w obiekcie typu `MovingGaps` musi zawierać bardzo dużo obiektów typu `Gap`. W rzeczywistości zawiera tylko trzy. Oznacza to, że w grze pojawiają się przed ptakiem bez przerwy te same trzy kolumny. Przed rozpoczęciem gry są one ustawione poza ekranem, daleko po prawej stronie, i w jednakowych odstępach od siebie. Po rozpoczęciu gry zaczynają przesuwać się w lewo. Jeżeli jakaś kolumna dojdzie do lewego brzegu ekranu i zniknie za nim, to jest od razu przestawiana na prawą stronę, za ostatnią kolumnę w szyku, w odpowiednim odstępie od niej. W ten sposób kolumny te poruszają się cyklicznie, w kółko, i sprawiają wrażenie, że jest ich nieskończenie wiele.

```python
class Gap:
    """Represents an empty rectangle between two pipes."""

    def __init__(self, x, y):
        if y >= GAP_Y_TOP_LIM and y <= GAP_Y_BOTTOM_LIM:
            self._x = x
            self._y = y
            self.vertical_velocity = random.choice([-1, 0, 1])
        else:
            raise ValueError("Error - gap can't go beyond screen")
    (...)
    def move_left(self):
        self.x -= GAP_SPEED

    def move_vertically(self):
        if self.y <= GAP_Y_TOP_LIM or self.y >= GAP_Y_BOTTOM_LIM:
            self.vertical_velocity *= -1
        self.y += self.vertical_velocity

    def respawn_after_last_gap(self, last_gap_x):
        self.x = last_gap_x + GAP_INTERVAL
        self.y = random.randint(GAP_Y_TOP_LIM, GAP_Y_BOTTOM_LIM)
        self.vertical_velocity = random.choice([-1, 0, 1])
    (...)
```

```python
class MovingGaps:
    """Represents the list of gaps moving in cycle in the left direction."""

    def __init__(self, gaps_num, init_x):
        if gaps_num > 0:
            self.init_x = init_x
            self.gaps = []
            for i in range(gaps_num):
                gap_x = init_x + i * GAP_INTERVAL
                gap_y = random.randint(GAP_Y_TOP_LIM, GAP_Y_BOTTOM_LIM)
                self.gaps.append(Gap(gap_x, gap_y))
            self.last_gap = self.gaps[-1]
            self.gap_ahead_of_bird = 0
        else:
            raise ValueError("Error - at least one gap is needed")
    (...)
    def move(self):
        for gap in self.gaps:
            if gap.right < 0:
                gap.respawn_after_last_gap(self.last_gap.x)
                self.last_gap = gap
            gap.move_left()
            gap.move_vertically()
    (...)
```

### Zapisywanie wyników

Jeżeli gracz zechce, to może zapisać swój wynik, tak aby był przez program pamiętany w kolejnych uruchomieniach. Wyniki zapisywane są do pliku *leaderboard.json*. Struktura i przykładowa zawartość tego pliku jest przedstawiona poniżej.

```json
[
    {
        "id": "kk2",
        "date": "25-12-2023 19:27:46",
        "score": 2
    },
    {
        "id": "fb6",
        "date": "25-12-2023 19:28:29",
        "score": 6
    },
    {
        "id": "go3",
        "date": "25-12-2023 19:29:49",
        "score": 3
    }
]
```

Jak widać, w pliku tym znajduje się lista obiektów. Każdy obiekt zawiera informacje o jednym, konkretnym wyniku uzyskanym i zapisanym przez gracza. Jak gracz zapisuje swój wynik, to tworzony jest nowy obiekt i dodawany jest do tej listy.

Poszczególne obiekty z powyższej listy są reprezentowane w programie przez obiekty klasy `LeaderboardEntry`. Cała lista z kolei jest reprezentowana przez obiekt klasy `Leaderboard`.

Atrybutami obiektów typu `LeaderboardEntry` są `id`, `date` oraz `score`. Atrybutem obiektu typu `Leaderboard` jest lista `entries`, czyli lista obiektów typu `LeaderboardEntry`.

Logika jest taka, że jak gracz zapisuje swój wynik, to tworzony jest nowy obiekt `LeaderboardEntry` i dodawany jest do listy `entries` zawartej w obiekcie `Leaderboard`. Następnie informacje z listy `entries` są zapisywane do pliku *leaderboard.json*. W tym celu wykonywane są dwa kroki. Najpierw obiekty `LeaderboardEntry` są serializowane do formatu JSON, czyli zamieniane są na słowniki za pomocą funkcji `LeaderboardEntry.to_dict(entry)`. Następnie obiekt `Leaderboard` jest serializowany do formatu JSON, czyli zamieniany jest na listę za pomocą funkcji `Leaderboard.to_list(leaderboard)`. Ostatecznie do pliku zapisywana jest lista słowników.

Jeżeli program zauważy, że plik *leaderboard.json* istnieje, to odczyta jego zawartość i w ten sposób będzie znał wszystkie wyniki zapisane wcześniej przez gracza. Aby odczytać zawartą w pliku listę słowników, program przeprowadzi proces odwrotny do tego opisanego powyżej, tzn. zamieni słowniki na obiekty `LeaderboardEntry` (funkcja `LeaderboardEntry.from_dict(entry)`), a listę na obiekt `Leaderboard` (funkcja `Leaderboard.from_list(leaderboard)`).

Jeżeli plik *leaderboard.json* nie istnieje, to program go utworzy przy pierwszej operacji zapisywania jakiej dokona gracz.

Najwyższy wynik zapisany w pliku *leaderboard.json* będzie wyświetlany na ekranie gry. Jeżeli zapisany zostanie wynik lepszy, to oczywiście na ekranie wszystko się zaaktualizuje.

```python
class LeaderboardEntry:
    """Represents info about one game try that is/will be in leaderboard.json"""

    def __init__(self, id, date, score):
        self.id = id
        self.date = date
        self.score = score

    @staticmethod
    def to_dict(entry):
        """Returns the dictionary representation of a LeaderboardEntry object."""
        return {"id": entry.id, "date": entry.date, "score": entry.score}

    @staticmethod
    def from_dict(entry):
        """Returns a LeaderboardEntry object from its dictionary representation."""
        return LeaderboardEntry(entry["id"], entry["date"], entry["score"])

    @staticmethod
    def get_id():
        """Opens a popup window with a text field to get an id from a player."""
        id = simpledialog.askstring("", "Enter your id:")
        return id
```

```python
class Leaderboard:
    """Represents the list of all game tries in leaderboard.json"""

    # self.entries is a list of LeaderboardEntry objects
    def __init__(self, entries=None):
        if entries == None:
            self.entries = []
        else:
            self.entries = entries

    def add_entry(self, entry):
        self.entries.append(entry)

    def get_best(self):
        if self.entries == []:
            return None
        else:
            return max(self.entries, key=lambda entry: entry.score)

    def print(self):
        print(json.dumps(Leaderboard.to_list(self), indent=4))

    @staticmethod
    def to_list(leaderboard):
        """Converts a Leaderboard object to its json representation."""
        return list(map(lambda x: LeaderboardEntry.to_dict(x), leaderboard.entries))

    @staticmethod
    def from_list(leaderboard):
        """Gets a Leaderboard object from its json representation."""
        return Leaderboard(list(map(lambda x: LeaderboardEntry.from_dict(x), leaderboard)))

    @staticmethod
    def save_to_json(leaderboard, path):
        """Saves the json representation of a Leaderboard object to a json file."""
        with open(path, "w") as leaderboard_json:
            json.dump(Leaderboard.to_list(leaderboard), leaderboard_json, indent=4)

    @staticmethod
    def get_from_json(path):
        """Returns a Leaderboard object based on its representation in a json file."""
        if os.path.exists(path):
            with open(path, "r") as leaderboard_json:
                json_data = json.load(leaderboard_json)
                return Leaderboard.from_list(json_data)
        else:
            return Leaderboard()
```

```python
(...)
leaderboard = Leaderboard.get_from_json(LEADERBOARD_PATH)
(...)
while True:
    (...)
            # Player pressed s - saving the score to the leaderboard
            if event.key == pygame.K_s:
                if game_state == GAME_END and not bird_falling:
                    id = LeaderboardEntry.get_id()
                    if id != None:
                        date = get_current_time()
                        leaderboard.add_entry(LeaderboardEntry(id, date, score.get_value()))
                        Leaderboard.save_to_json(leaderboard, LEADERBOARD_PATH)
                        best_try_info.text = "Best: " + str(leaderboard.get_best().score)
                        (...)
            # Player pressed p - displaying leaderboard in console
            if event.key == pygame.K_p:
                    print("================================================")
                    leaderboard.print()
                    print("================================================")
                    print()
    (...)
```

## Podsumowanie

Pomysł na implementację i sama implementacja jest całkowicie autorska. Podczas pisania kodu zwracano uwagę na to, by używać obiektowości Pythona i żeby uwzględnić w programie pracę z plikami. Prawdopodobnie wiele rzeczy można było zrobić i prościej i krócej i wydajniej, ale wydaje się, że kod działa poprawnie i nie ma żadnych bugów.

Możliwe jednak, że w grze wystąpi jeden mały problem, który pojawiał się podczas testowania gry - rury mogą się lekko lagować przy poruszaniu się w lewo. Możliwe, że problem ten jest powodowany niewydajnym kodem. Mimo wszystko problem ten, jeżeli wystąpi, to nie powinien przeszkadzać w rozgrywce i sprawiać, że gra stanie się niegrywalna.

## Źródła

- oryginalna gra (inspiracja): https://flappybird.io/
- obrazki: https://github.com/samuelcust/flappy-bird-assets