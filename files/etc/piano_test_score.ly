\version "2.26" 
\include "lilypond-book-preamble.ly"
    
color = #(define-music-function (parser location color) (string?) #{
        \once \override NoteHead.color = #(x11-color color)
        \once \override Stem.color = #(x11-color color)
        \once \override Rest.color = #(x11-color color)
        \once \override Beam.color = #(x11-color color)
     #})
    
\header { 
 title = "Music21 Fragment"   
  
  } 
 
\score  { 
 
      << \new Staff  = yzfxcafbfzxwa { \key c \major 
             \time 4/4
             c' 4  
             d' 4  
             e' 4  
             f' 4  
             \bar "|"  %{ end measure 1 %} 
             g' 4  
             a' 4  
             g' 4  
             f' 4  
             \bar "|"  %{ end measure 2 %} 
             e' 4  
             d' 4  
             c' 4  
             d' 4  
             \bar "|"  %{ end measure 3 %} 
             e' 4  
             c' 4  
             g 4  
             c' 4  
             \bar "|"  %{ end measure 4 %} 
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
 
