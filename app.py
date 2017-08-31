"""Written by:  Christopher F. French
        email:  cffrench.writes@gmail.com
         date:  2017
      version:  0.1.0

This is a pre-alpha, broken, version of BayesBall.

--------------------------------------------------------------------------------
This file is part of BayesBall.

BayesBall is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

BayesBall is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with BayesBall.  If not, see <http://www.gnu.org/licenses/>.
--------------------------------------------------------------------------------
"""
import curses
from itertools import count
from game import BaseBallGame
from helpers import match, match_array
from context import outcome_records
from copy import deepcopy

def flatten(d, label):
    assert isinstance(d, dict)
    catch = []
    for k, v in d.items():
        if isinstance(v, dict):
            v = deepcopy(v)
            if label:
                catch.extend(flatten(v, label))
            else:
                v = deepcopy(v)
                catch.extend(flatten(v, k))
            else:
                catch.append((label, v))
    return catch

                
event_map = flatten(outcome_records, None)

def get_rec_label(rec):
    global event_map
    rec_name = 'missing'
    for label, rec_type in event_map:
        if match(rec, rec_type):
            rec_name = label
    return rec_name

def app(c, home_p, main_p, away_p):
    """Simple curses-based application to watch a BayesBall simulation.

    This primary purpose of this curses program is to help with debugging,
    without worrying too much about the UX experience. It should, ideally,
    simply display, in order, the deque stack for each play, and the currrent
    game state. 
    
    Warning: This only works on Unix -- it won't work in a Windows shell,
    but feel free to change that if you want.

            
    To do:
    ======
    [ ] Right now, there is something wrong with how the curses
        windows get refreshed/displayed. I will fix it when I have
        time, but first I need to go back and fix game.py, which I
        also don't have time to do.
    [ ] Write a box score in curses
    [ ] write options to swap/sub players.
    [ ] write another screen with player stats for the current game:
        e.g., a bottom screen to display batter at-bats, hits, walks,
        and pitcher stikes, etc.

        Also: DOING THIS will also help debug game.py!

    [ ] (major) Re-write this entire app to update a Jinja2 template,
        and display the game results as a webpage, which would also
        have JS code for managing each team, etc.
    [ ] (major) Use Flask with a db to create a way to visualize the
        results of a simulated season of games.

    """
    curses.start_color()
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    """Create three windows:

    A screren for each team, and one for
    presenting the current gamestate.
    """
    home_screen = curses.newwin(*home_p)
    main_screen = curses.newwin(*main_p)
    away_screen = curses.newwin(*away_p)
    home_screen.border()
    away_screen.border()
    teams = [
            ('Home', 'home', home_screen),
            ('Away', 'away', away_screen)
    ]
    """Helper functions"""
    def refresh_all():
        """Refresh all three windows"""
        home_screen.refresh()
        away_screen.refresh()
        main_screen.refresh()

    def print_team(game, side):
        """Print team info in a side screen"""
        win = side[2]
        gs = game.gamestate
        team = getattr(game, side[1])
        team_batter_pos = getattr(game, '_'+side[1]+'_pos')
        win.addstr(1, 1, side[0]+' Team:')
        win.addstr(2, 1, team.name)
        win.addstr(4, 1, 'Score: '+str(getattr(gs.score, side[1])))
        win.addstr(6, 1, '__Lineup__({})'.format(team_batter_pos+1))
        n = 7
        for x, p in enumerate(team.lineup):
            color = 2 if x == team_batter_pos else 1
            player_info = str(n-6)+': '+str(p.num)+' '+str(p.posname)
            win.addstr(n, 2, player_info, curses.color_pair(color))
            n+=1

    def print_team_info(game):
        """Print both side-screen windows"""
        home_screen.erase()
        away_screen.erase()
        home_screen.border()
        away_screen.border()
        print_team(game, teams[0])
        print_team(game, teams[1])
        
    def print_game_info(game, history):
        """Print gamestate and current batter/pitcher info"""
        main_screen.erase()
        gs = game.gamestate
        strikes = str(gs.count.strikes)
        balls = str(gs.count.balls)
        outs = str(gs.count.outs)
        first = str(gs.bases.first)
        second = str(gs.bases.second)
        third = str(gs.bases.third)
        inning = str(gs.inning.inning)
        order = str(gs.inning.order)

        bot_msg = 'Batter: {} {}  Pitcher: {} {}'
        main_screen.addstr(
            28, 4, bot_msg.format(
                game.batter.num, game.batter.posname,
                game.pitcher.num, game.pitcher.posname
            )
        )

        inning_info = order+' of inning '+inning
        main_screen.addstr(4, 4, inning_info)

        count_info = 'Strikes: '+strikes+' Balls: '+balls+' Outs: '+outs
        main_screen.addstr(6, 4, count_info)

        base_info = '3rd: '+third+' 2nd: '+second+' First: '+first 
        main_screen.addstr(8, 4, base_info)

        
        
        if history:
            n = 10
            deque_info = '{} action(s) took place this play.'
            deque_msg = deque_info.format(len(history))
            main_screen.addstr(n, 4, deque_msg)
            for rec in history:
                n+=2
                rec_name = get_rec_label(rec)
                main_screen.addstr(
                    n, 4, '{} event: {}'.format(rec_name, rec)
                )

    def play_and_display_game():
        """The main BayesGame loop"""
        game = BaseBallGame(None, None, False)
        print_team_info(game)
        main_screen.addstr(8, 4, 'press any key to start!')
        refresh_all()
        innings = count(1, .5)
        for I in innings:
            game.upkeep(I)
            if game.win(I):
                break
            print_team_info(game)
            refresh_all()
            main_screen.getkey()
            while game.gamestate.count.outs < 3:
                print_game_info(game, game.play)
                print_team_info(game)
                refresh_all()
                main_screen.getkey()
                
        print_team_info(game)
        main_screen.addstr(20, 4, game.win_msg)
        main_screen.addstr(22, 4, 'press any key to exit.')
        main_screen.move(22, 30)
        refresh_all()
        main_screen.getkey()
        
    play_and_display_game()
                
if __name__=='__main__':
    def start_curses():
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        
        team_screen_width = 20
        team_screen_height = 30

        main_screen_width = 40
        main_screen_height = 30

        home_screen_x = 0
        home_screen_y = 0

        home_params = [
            team_screen_height,
            team_screen_width,
            home_screen_y,
            home_screen_x
        ]

        main_params = [
            main_screen_height,
            main_screen_width,
            home_screen_y,
            home_screen_x+team_screen_width
        ]

        away_params = [
            team_screen_height,
            team_screen_width,
            home_screen_y,
            home_screen_x+team_screen_width+main_screen_width
        ]

        return (stdscr, home_params, main_params, away_params)

    def end_curses(stdscr):
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    """Start the BayesGame!"""
    args = start_curses()
    try:
        app(*args)
    except:
        end_curses(args[0])
        exit(1)
    end_curses(args[0])