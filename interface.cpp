//#include "interface.h"
//
//Fl_Window* main_window = (Fl_Window*)0;
//
////buttons
//Fl_Button* play_button = (Fl_Button*)0;
//Fl_Button* pause_button = (Fl_Button*)0;
//Fl_Button* reset_button = (Fl_Button*)0;
//
//Fl_Window* make_window()
//{
//    Fl_Window* w;
//    {
//        Fl_Window* o = main_window = new Fl_Window(741, 622, "Video Player");
//        w = o;
//        {
//            {
//                Fl_Button* o = play_button = new Fl_Button(500, 575, 35, 25, "@>");
//                o->labeltype(FL_SYMBOL_LABEL);
//                o->labelsize(12);
//                o->callback((Fl_Callback*)play_callback, (void*)(0));
//            }
//            {
//                Fl_Button* o = pause_button = new Fl_Button(430, 575, 35, 25, "@||");
//                o->labeltype(FL_SYMBOL_LABEL);
//                o->labelsize(12);
//                o->callback((Fl_Callback*)pause_callback);
//            }
//            {
//                Fl_Button* o = reset_button = new Fl_Button(465, 575, 35, 25, "@|<");
//                o->labeltype(FL_SYMBOL_LABEL);
//                o->labelsize(12);
//                o->callback((Fl_Callback*)reset_callback);
//            }
//        }
//    }
//}