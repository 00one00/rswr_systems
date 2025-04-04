from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.customer_portal.models import CustomerUser
from .models import ReferralCode, Referral, Reward, RewardOption, RewardRedemption
import uuid
import random
import string
from django.contrib import messages
from .services import RewardFulfillmentService

# Helper functions
def generate_unique_code(length=8):
    """Generate a unique alphanumeric code"""
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        if not ReferralCode.objects.filter(code=code).exists():
            return code

# Referral code management
@login_required
def generate_referral_code(request):
    """Generate a new referral code for the logged-in user"""
    customer_user = CustomerUser.objects.get(user=request.user)
    
    # Check if user already has a referral code
    existing_code = ReferralCode.objects.filter(customer_user=customer_user).first()
    
    if request.method == 'POST':
        if existing_code:
            return JsonResponse({
                'success': False,
                'message': 'You already have a referral code',
                'code': existing_code.code
            })
        
        # Generate new code
        code = generate_unique_code()
        referral_code = ReferralCode.objects.create(
            code=code,
            customer_user=customer_user
        )
        
        # Redirect back to the same page to show the new code
        return redirect('generate_referral_code')
    
    # GET request - render the form
    return render(request, 'customer_portal/referrals/generate_code.html', {
        'existing_code': existing_code.code if existing_code else None
    })

@login_required
def referral_code(request):
    """Get the current user's referral code"""
    customer_user = CustomerUser.objects.get(user=request.user)
    referral_code = ReferralCode.objects.filter(customer_user=customer_user).first()
    
    if referral_code:
        return JsonResponse({
            'success': True,
            'code': referral_code.code
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'No referral code found'
        })

# Referral tracking
@login_required
def referral_tracking(request):
    """Track a successful referral"""
    if request.method == 'POST':
        code = request.POST.get('code')
        if not code:
            return JsonResponse({'success': False, 'message': 'Referral code is required'})
        
        try:
            referral_code = ReferralCode.objects.get(code=code)
            customer_user = CustomerUser.objects.get(user=request.user)
            
            # Ensure users can't refer themselves
            if referral_code.customer_user == customer_user:
                return JsonResponse({'success': False, 'message': 'You cannot refer yourself'})
            
            # Check if this referral already exists
            if Referral.objects.filter(referral_code=referral_code, customer_user=customer_user).exists():
                return JsonResponse({'success': False, 'message': 'This referral has already been processed'})
            
            # Create the referral
            Referral.objects.create(
                referral_code=referral_code,
                customer_user=customer_user
            )
            
            # Give points to the referrer
            referrer = referral_code.customer_user
            reward, created = Reward.objects.get_or_create(customer_user=referrer)
            reward.points += 500  # Assume 500 points per referral
            reward.save()
            
            return JsonResponse({'success': True, 'message': 'Referral processed successfully'})
            
        except ReferralCode.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid referral code'})
    
    return JsonResponse({'success': False, 'message': 'Only POST method is allowed'})

@login_required
def referral_history(request):
    """Get referral history for the current user"""
    customer_user = CustomerUser.objects.get(user=request.user)
    
    # Get the user's referral code
    referral_code = ReferralCode.objects.filter(customer_user=customer_user).first()
    
    if referral_code:
        # Get all referrals using this code
        referrals = Referral.objects.filter(referral_code=referral_code).order_by('-created_at')
        
        context = {
            'referrals': referrals,
            'referral_code': referral_code.code
        }
        
        return render(request, 'customer_portal/referrals/dashboard.html', context)
    else:
        # User doesn't have a referral code yet
        return render(request, 'customer_portal/referrals/dashboard.html', {'has_code': False})

@login_required
def referral_stats(request):
    """Get stats about the user's referrals"""
    customer_user = CustomerUser.objects.get(user=request.user)
    referral_code = ReferralCode.objects.filter(customer_user=customer_user).first()
    
    if not referral_code:
        return JsonResponse({
            'success': False,
            'message': 'No referral code found'
        })
    
    # Count referrals
    total_referrals = Referral.objects.filter(referral_code=referral_code).count()
    
    # Get reward points
    reward = Reward.objects.filter(customer_user=customer_user).first()
    points = reward.points if reward else 0
    
    return JsonResponse({
        'success': True,
        'total_referrals': total_referrals,
        'points': points,
        'code': referral_code.code
    })

@login_required
def referral_leaderboard(request):
    """View top referrers"""
    # Get referral counts for each user
    top_referrers = []
    
    for code in ReferralCode.objects.all():
        count = Referral.objects.filter(referral_code=code).count()
        if count > 0:
            top_referrers.append({
                'user': code.customer_user,
                'count': count
            })
    
    # Sort by count, take top 10
    top_referrers = sorted(top_referrers, key=lambda x: x['count'], reverse=True)[:10]
    
    return render(request, 'customer_portal/referrals/leaderboard.html', {'top_referrers': top_referrers})

# Reward management
@login_required
def reward_balance(request):
    """Get the current user's reward balance"""
    customer_user = CustomerUser.objects.get(user=request.user)
    reward = Reward.objects.filter(customer_user=customer_user).first()
    
    points = reward.points if reward else 0
    
    return JsonResponse({
        'success': True,
        'points': points
    })

@login_required
def reward_history(request):
    """View reward history"""
    customer_user = CustomerUser.objects.get(user=request.user)
    redemptions = RewardRedemption.objects.filter(
        reward__customer_user=customer_user
    ).order_by('-created_at')
    
    return render(request, 'customer_portal/referrals/rewards.html', {
        'redemptions': redemptions
    })

@login_required
def reward_options(request):
    """List available reward options"""
    options = RewardOption.objects.all().order_by('points_required')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON for API requests
        return JsonResponse({
            'success': True,
            'options': [
                {
                    'id': option.id,
                    'name': option.name,
                    'description': option.description,
                    'points_required': option.points_required
                }
                for option in options
            ]
        })
    
    # Return HTML for direct browser requests
    return render(request, 'customer_portal/referrals/rewards.html', {
        'reward_options': options
    })

@login_required
@require_POST
def redeem_reward(request):
    """Redeem points for a reward"""
    option_id = request.POST.get('option_id')
    
    if not option_id:
        messages.error(request, 'Reward option is required')
        return redirect('referral_rewards')
    
    try:
        customer_user = CustomerUser.objects.get(user=request.user)
        reward_option = RewardOption.objects.get(id=option_id)
        
        # Get or create user reward record
        reward, created = Reward.objects.get_or_create(customer_user=customer_user)
        
        # Check if user has enough points
        if reward.points < reward_option.points_required:
            messages.error(request, f'Not enough points. You need {reward_option.points_required} points, but have {reward.points}.')
            return redirect('referral_rewards')
        
        # Create redemption record
        redemption = RewardRedemption.objects.create(
            reward=reward,
            reward_option=reward_option,
            status='PENDING'
        )
        
        # Deduct points
        reward.points -= reward_option.points_required
        reward.save()

        # Assign a technician to fulfill this redemption
        assigned_technician = RewardFulfillmentService.assign_technician(redemption)
        
        if assigned_technician:
            messages.success(
                request, 
                f'Successfully redeemed {reward_option.name}. A technician will be assigned to fulfill your reward.'
            )
        else:
            messages.success(
                request, 
                f'Successfully redeemed {reward_option.name}. Your request is pending technician assignment.'
            )
        
        return redirect('referral_rewards')
        
    except RewardOption.DoesNotExist:
        messages.error(request, 'Invalid reward option')
        return redirect('referral_rewards')
    except Exception as e:
        messages.error(request, f'An error occurred while processing your redemption: {str(e)}')
        return redirect('referral_rewards')

@login_required
def referral_rewards(request):
    """View dashboard for rewards system"""
    customer_user = CustomerUser.objects.get(user=request.user)
    
    # Get reward points
    reward = Reward.objects.filter(customer_user=customer_user).first()
    points = reward.points if reward else 0
    
    # Get referral code
    referral_code = ReferralCode.objects.filter(customer_user=customer_user).first()
    code = referral_code.code if referral_code else None
    
    # Get referral count
    referral_count = 0
    if referral_code:
        referral_count = Referral.objects.filter(referral_code=referral_code).count()
    
    # Get reward options
    reward_options = RewardOption.objects.all().order_by('points_required')
    
    # Get redemption history
    redemptions = RewardRedemption.objects.filter(
        reward__customer_user=customer_user
    ).order_by('-created_at')[:5]  # Show only the 5 most recent
    
    context = {
        'points': points,
        'referral_code': code,
        'referral_count': referral_count,
        'reward_options': reward_options,
        'redemptions': redemptions
    }
    
    return render(request, 'customer_portal/referrals/dashboard.html', context)

@login_required
def referral_rewards_history(request):
    """View reward redemption history"""
    customer_user = CustomerUser.objects.get(user=request.user)
    redemptions = RewardRedemption.objects.filter(
        reward__customer_user=customer_user
    ).order_by('-created_at')
    
    return render(request, 'customer_portal/referrals/rewards.html', {
        'redemptions': redemptions
    })

@login_required
def referral_rewards_balance(request):
    """Get the current reward balance"""
    customer_user = CustomerUser.objects.get(user=request.user)
    reward = Reward.objects.filter(customer_user=customer_user).first()
    points = reward.points if reward else 0
    
    return JsonResponse({
        'success': True,
        'points': points
    })
