
from django.contrib.auth import authenticate, login, logout, get_user
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django import forms
from django.forms import modelform_factory
from .models import Auction, User, Category, Bid, Comment
from .forms import AuctionForm, BidForm
from django.db.models import Max



def index(request):
 
    active_auctions = Auction.objects.filter(active=True)

    auctions = auctions_list_with_max_bids(active_auctions)

    return render(request, "auctions/index.html", {
        "auctions": auctions,
        "page_header": "Active auctions"
    })


@login_required
def my_lots(request):
    current_user = get_user(request=request) 
    auction = Auction.objects.filter(author=current_user)  
    auctions = auctions_list_with_max_bids(auction)
    return render(request, "auctions/index.html", {
        "auctions": auctions,
        "page_header": "My lots"
    }) 


def categoties(request):
    category = Category.objects.all()
    return render(request, "auctions/categories.html", {
        "categories": category
    })


def categoty_auctions(request, category_id):
    category = Category.objects.get(pk=category_id) 
    auction = Auction.objects.filter(category=category)
    auctions = auctions_list_with_max_bids(auction)
    return render(request, "auctions/index.html", {
        "auctions": auctions,
        "page_header": f"Auctions in category {category.name}"
    }) 


@login_required
def watchlist(request):
    current_user = get_user(request=request)
    auctions = Auction.objects.filter(watched_by_users=current_user)
    auctions = auctions_list_with_max_bids(auctions)
    return render(request, "auctions/index.html", {
        "auctions": auctions,
        "page_header": "My watchlist"
    }) 


@login_required
def related_auctions(request):
    current_user = get_user(request=request)
    auctions = set()
    for bid in Bid.objects.select_related("auction").filter(author=current_user):
        auctions.add(bid.auction)
   
    auctions = auctions_list_with_max_bids(auctions)
   
    return render(request, "auctions/index.html", {
        "auctions": auctions,
        "page_header": "Auctions with my bids"
    }) 


@login_required
def add_to_watchlist(request, auction_id):
    auction = Auction.objects.get(pk=auction_id)
    current_user = get_user(request=request)
    auction.watched_by_users.add(current_user)
    auction.save()
    return HttpResponseRedirect(reverse("auction",kwargs={"auction_id": auction_id}))


@login_required
def remove_from_watchlist(request, auction_id):
    auction = Auction.objects.get(pk=auction_id)
    current_user = get_user(request=request)
    auction.watched_by_users.remove(current_user)
    auction.save()
    return HttpResponseRedirect(reverse("auction",kwargs={"auction_id": auction_id}))


@login_required
def close_auction(request, auction_id):
    auction = Auction.objects.get(pk=auction_id)
    current_user = get_user(request=request)
    if auction.author == current_user:
        auction.active = False
        auction.save()
    return HttpResponseRedirect(reverse("auction",kwargs={"auction_id": auction_id}))


def login_view(request):
    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def new(request):
    if request.method == "POST" and request.user.is_authenticated:

        form = AuctionForm(request.POST)
        item_name = request.POST["item_name"]
        item_description = request.POST["item_description"]
        start_bid = request.POST["start_bid"]
        picture_url = request.POST["picture_url"]
        category_pk = request.POST["category"]

        if float(start_bid) < 0:
            return render(request, "auctions/new.html", {
            "form": form,
            "message": True
        })

        if category_pk != "":
            category = Category.objects.get(pk=category_pk)
        else:
            category = None

        auction = Auction(item_name=item_name, item_description=item_description,
                    start_bid=start_bid, picture_url=picture_url, category=category,
                    author=request.user)

        if form.is_valid():
            auction.save()
            return HttpResponseRedirect(reverse("index"), {
                "message": f"{auction}"
            })
        else:
            return HttpResponseRedirect(reverse("new"), {
                "form": form,
                "message": True
            })
    else:
        form = AuctionForm()
        return render(request, "auctions/new.html", {
            "form": form,
            "message": False
        })


def auction(request, auction_id):
    auction = Auction.objects.get(pk=auction_id)
    authorFullName = auction.author.get_full_name()
    if authorFullName == '':
        authorFullName = auction.author.username
    start_bid = auction.start_bid
    current_user = get_user(request=request)
    bid_error_message = ''
    
    bidform = BidForm()
    lastbid = get_max_bid(auction)
    winner_user = False
    if lastbid != None:
        if not auction.active and lastbid.author == current_user:
            winner_user = True        
        lastbid = lastbid.amount

    comments = Comment.objects.filter(auction=auction).order_by("-date")

    is_watched = auction_is_watched(auction, current_user)

    if request.method == "POST" and "amount" in request.POST:
        amount = float(request.POST["amount"])

        if lastbid == None and amount >= start_bid:
            save_new_bid(author=current_user, amount=amount, auction=auction)
        elif lastbid != None:
            if amount > lastbid:
                save_new_bid(author=current_user, amount=amount, auction=auction)
            else:
                bid_error_message = f'Bid {amount} is less than current bid {lastbid}. Please make bigger bid.'
        else:
            bid_error_message = f'Bid {amount} is less than start bid {start_bid}. Please make bigger bid.'

        return render(request, "auctions/auction.html", {
            "auction": auction,
            "authorFullName": authorFullName,
            "bidform": bidform,
            "current_bid": amount if bid_error_message == '' else lastbid,
            "bid_error_message": bid_error_message,
            "bid_successfull": True if bid_error_message == '' else False,
            "comments": comments,
            "winner_user": winner_user,
            "is_watched": is_watched
        })
    if request.method == "POST" and "comment_text" in request.POST:
        comment_text = request.POST["comment_text"]
        new_comment = Comment(author=current_user, auction=auction, text=comment_text)
        new_comment.save()
        comments = Comment.objects.filter(auction=auction).order_by("-date")

    return render(request, "auctions/auction.html", {
        "auction": auction,
        "authorFullName": authorFullName,
        "bidform": bidform,
        "current_bid": lastbid,
        "comments": comments,
        "winner_user": winner_user,
        "is_watched": is_watched
    })


def save_new_bid(author, amount, auction):
    new_bid = Bid(author=author, amount=amount, auction=auction)
    new_bid.save()


def auction_is_watched(auction, user):
   
    auction = User.objects.filter(watched_list=auction)

    if user in auction:
        return True
    else:
        return False


def get_max_bid(auction):
    bids = Bid.objects.filter(auction=auction)
    bids.order_by('amount')
    lastbid = bids.last()
    return lastbid


def auctions_list_with_max_bids(auctions):
    auctionslist = []
    for auction in auctions:
        maxbid = get_max_bid(auction=auction)
        if maxbid == None:
            maxbid = auction.start_bid
        else:
            maxbid = maxbid.amount

        auction_set = {
            "auction": auction,
            "maxbid": maxbid
        }
        auctionslist.append(auction_set)
    return auctionslist