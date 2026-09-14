\version "2.26" 
\include "lilypond-book-preamble.ly"
    
color = #(define-music-function (parser location color) (string?) #{
        \once \override NoteHead.color = #(x11-color color)
        \once \override Stem.color = #(x11-color color)
        \once \override Rest.color = #(x11-color color)
        \once \override Beam.color = #(x11-color color)
     #})
    
\header { } 
\score  { 
 
      << \new Staff  = melody { d' 4  
             c' 4  
             g' 4  
             f' 4  
             \key c \major 
             \time 4/4
             \bar "|"  %{ end measure 1 %} 
             f' 4  
             e' 4  
             d' 4  
             d'' 4  
             \bar "|"  %{ end measure 2 %} 
             d' 4  
             b' 4  
             c' 4  
             c' 4  
             \bar "|"  %{ end measure 3 %} 
             d' 4  
             f' 4  
             f' 4  
             d'' 4  
             \bar "|"  %{ end measure 4 %} 
             c' 4  
             d'' 4  
             f' 4  
             d'' 4  
             \bar "|"  %{ end measure 5 %} 
             b' 4  
             f' 4  
             c'' 4  
             g' 4  
             \bar "|"  %{ end measure 6 %} 
             c' 4  
             e' 4  
             b' 4  
             a' 4  
             \bar "|"  %{ end measure 7 %} 
             g' 4  
             e' 4  
             f' 4  
             a' 4  
             \bar "|"  %{ end measure 8 %} 
             d' 4  
             d' 4  
             b' 4  
             d' 4  
             \bar "|"  %{ end measure 9 %} 
             a' 4  
             a' 4  
             g' 4  
             c' 4  
             \bar "|"  %{ end measure 10 %} 
             c'' 4  
             d'' 4  
             d' 4  
             b' 4  
             \bar "|"  %{ end measure 11 %} 
             d' 4  
             d'' 4  
             g' 4  
             a' 4  
             \bar "|"  %{ end measure 12 %} 
             f' 4  
             d' 4  
             c' 4  
             f' 4  
             \bar "|"  %{ end measure 13 %} 
             g' 4  
             d' 4  
             f' 4  
             d' 4  
             \bar "|"  %{ end measure 14 %} 
             b' 4  
             g' 4  
             c'' 4  
             a' 4  
             \bar "|"  %{ end measure 15 %} 
             e' 4  
             a' 4  
             a' 4  
             f' 4  
             \bar "|"  %{ end measure 16 %} 
             g' 4  
             d' 4  
             e' 4  
             d'' 4  
             \bar "|"  %{ end measure 17 %} 
             f' 4  
             e' 4  
             c'' 4  
             b' 4  
             \bar "|"  %{ end measure 18 %} 
             g' 4  
             d'' 4  
             f' 4  
             a' 4  
             \bar "|"  %{ end measure 19 %} 
             c' 4  
             f' 4  
             c' 4  
             a' 4  
             \bar "|"  %{ end measure 20 %} 
             b' 4  
             g' 4  
             d' 4  
             f' 4  
             \bar "|"  %{ end measure 21 %} 
             a' 4  
             f' 4  
             c'' 4  
             b' 4  
             \bar "|"  %{ end measure 22 %} 
             c'' 4  
             e' 4  
             g' 4  
             e' 4  
             \bar "|"  %{ end measure 23 %} 
             f' 4  
             d'' 4  
             d'' 4  
             g' 4  
             \bar "|"  %{ end measure 24 %} 
              } 
            
 
        >>
      
  } 
 
\paper { }
\layout {
  \context {
    \RemoveEmptyStaves
    \override VerticalAxisGroup.remove-first = ##t
  }
 }
 
