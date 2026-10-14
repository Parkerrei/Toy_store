# Django-Project-Toy_Store
Site Link : peter.pythonanywhere.com

Backend:
1)Solved race condition
2)Solved n+1 problem
3)Optimize query by using select related
4)added login system
5)added user singup system
6)Used atomicity for operation rollback if code breaks in half way
7)cart system for anonymous user as well as login user
8)Integrated fully functional razorypay system 
9)handled crytographic key sent by Razorpay for authentication
10)handled user logout system 
11)handled next parameter in login system to redirect anonymous user once they login
12)Used pagination for per page reload inspired from amazon style ui
13)Used django form for data validation
14)wrote custom command line to automatically upload images from a folder
15)Used Django signal to merge anonymous cart once they login
16)practised by building using DRY principle
17)Used LocMemcache for repeated queried unchangeable data just for testing and learning caching in django , later transition to redis once in deployment mode

FRONTEND:
1)started with basic js,css and html
2)Used Html5 , internal js and internal Css
3)used fetch for asynchronous request
4)learned to send xmlhttp request to backend in order to perform operation automatically rather than user has to do it e.g when user scrolls and reach end of the page ,product will automatically load just like amazon and other ecommerce site do 
