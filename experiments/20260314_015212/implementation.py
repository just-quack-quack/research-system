"""
Multi-modal Foundation Model for Humanoid Control
Combines VLM (vision), tactile, and audio sensing for richer understanding

Paper: "Multi-modal Foundation Models for Humanoid Control"
Gap: Most humanoid foundation models focus on vision, fewer on audio/tactile integration
Idea: Combine VLM with tactile and audio sensing for richer understanding
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, Optional
import numpy as np

class MultiModalHumanoidController(nn.Module):
    """
    Multi-modal controller that combines vision, tactile, and audio inputs
    for comprehensive humanoid robot understanding and control.
    """

    def __init__(
        self,
        vision_dim: int = 768,        # CLIP/ViT feature dimension
        tactile_dim: int = 128,         # Tactile sensor features
        audio_dim: int = 256,          # Audio spectrogram features
        hidden_dim: int = 1024,        # Hidden dimension
        action_dim: int = 56,           # Humanoid action space (approx)
        num_heads: int = 8,            # Attention heads
        dropout: float = 0.1
    ):
        super().__init__()

        # 1. Modality-specific encoders
        self.vision_encoder = nn.Sequential(
            nn.Linear(vision_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, hidden_dim),  # Output full hidden_dim
        )

        self.tactile_encoder = nn.Sequential(
            nn.Linear(tactile_dim, hidden_dim // 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 4, hidden_dim // 2),
        )

        self.audio_encoder = nn.Sequential(
            nn.Linear(audio_dim, hidden_dim // 4),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 4, hidden_dim // 2),
        )

        # 2. Cross-modal attention (vision attends to tactile/audio)
        # Project all features to same dimension for attention
        self.tactile_projection = nn.Linear(hidden_dim // 2, hidden_dim)
        self.audio_projection = nn.Linear(hidden_dim // 2, hidden_dim)

        self.cross_attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            dropout=dropout,
            batch_first=True
        )

        # 3. Fusion network (combine all modalities)
        self.fusion_network = nn.Sequential(
            nn.Linear(hidden_dim + hidden_dim // 2 + hidden_dim // 2, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
        )

        # 4. Policy head (output actions)
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, action_dim),
            nn.Tanh()  # Actions typically bounded
        )

        # 5. Value head (for RL training)
        self.value_head = nn.Linear(hidden_dim // 2, 1)

        # Learnable modality weights (importance of each modality)
        self.modality_weights = nn.Parameter(
            torch.ones(3) / 3  # Initialize equal weights
        )

    def forward(
        self,
        vision: torch.Tensor,      # [batch, vision_dim]
        tactile: torch.Tensor,    # [batch, tactile_dim]
        audio: torch.Tensor,       # [batch, audio_dim]
        return_attentions: bool = False
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], Dict]:
        """
        Forward pass through multi-modal controller.

        Returns:
            actions: [batch, action_dim]
            values: [batch, 1]
            info: Dictionary with modality features and attentions
        """

        batch_size = vision.shape[0]

        # 1. Encode each modality
        vision_features = self.vision_encoder(vision)      # [B, H/2]
        tactile_features = self.tactile_encoder(tactile)  # [B, H/2]
        audio_features = self.audio_encoder(audio)          # [B, H/2]

        # 2. Apply learnable modality weights
        vision_features = vision_features * self.modality_weights[0]
        tactile_features = tactile_features * self.modality_weights[1]
        audio_features = audio_features * self.modality_weights[2]

        # 3. Project tactile/audio to same dimension for cross-attention
        tactile_proj = self.tactile_projection(tactile_features)  # [B, H]
        audio_proj = self.audio_projection(audio_features)          # [B, H]

        # 4. Stack for cross-attention
        # Vision acts as query, tactile/audio as key/value
        combined_kv = torch.cat([
            tactile_proj.unsqueeze(1),
            audio_proj.unsqueeze(1)
        ], dim=1)  # [B, 2, H]

        vision_query = vision_features.unsqueeze(1)  # [B, 1, H]

        attended_features, attention_weights = self.cross_attention(
            vision_query,
            combined_kv,
            combined_kv
        )  # attended_features: [B, 1, H/2]

        # Remove sequence dimension
        attended_features = attended_features.squeeze(1)  # [B, H/2]

        # 4. Fuse all modalities
        fused = torch.cat([
            vision_features,
            attended_features
        ], dim=1)  # [B, 3H/2]

        fusion_output = self.fusion_network(fused)  # [B, H/2]

        # 5. Generate actions and values
        actions = self.policy_head(fusion_output)  # [B, action_dim]
        values = self.value_head(fusion_output)   # [B, 1]

        info = {
            'vision_features': vision_features,
            'tactile_features': tactile_features,
            'audio_features': audio_features,
            'attended_features': attended_features,
            'fusion_output': fusion_output,
            'modality_weights': F.softmax(self.modality_weights, dim=0),
        }

        if return_attentions:
            info['attention_weights'] = attention_weights

        return actions, values, info


class MultiModalHumanoidControllerSmall(MultiModalHumanoidController):
    """Smaller version for faster experimentation"""

    def __init__(self, **kwargs):
        kwargs['hidden_dim'] = kwargs.get('hidden_dim', 512)
        super().__init__(**kwargs)


def create_default_model() -> MultiModalHumanoidController:
    """Create a default model for experimentation"""
    return MultiModalHumanoidController(
        vision_dim=768,
        tactile_dim=128,
        audio_dim=256,
        hidden_dim=1024,
        action_dim=56,
        num_heads=8,
        dropout=0.1
    )


def test_forward_pass():
    """Test the model with random inputs"""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = create_default_model().to(device)

    # Random inputs (simulating batch of 4)
    batch_size = 4
    vision = torch.randn(batch_size, 768).to(device)
    tactile = torch.randn(batch_size, 128).to(device)
    audio = torch.randn(batch_size, 256).to(device)

    # Forward pass
    actions, values, info = model(vision, tactile, audio, return_attentions=True)

    print(f"✓ Forward pass successful!")
    print(f"  Actions shape: {actions.shape}")
    print(f"  Values shape: {values.shape}")
    print(f"  Modality weights: {info['modality_weights'].detach().cpu().numpy()}")
    print(f"  Attention weights shape: {info['attention_weights'].shape}")

    # Verify outputs
    assert actions.shape == (batch_size, 56), f"Actions shape mismatch: {actions.shape}"
    assert values.shape == (batch_size, 1), f"Values shape mismatch: {values.shape}"

    return actions, values, info


def train_step(
    model: MultiModalHumanoidController,
    optimizer: torch.optim.Optimizer,
    vision: torch.Tensor,
    tactile: torch.Tensor,
    audio: torch.Tensor,
    target_actions: torch.Tensor,
    target_values: torch.Tensor
) -> Dict[str, float]:
    """
    Single training step (behavior cloning style).

    Returns:
        Dictionary with loss components
    """

    # Forward pass
    pred_actions, pred_values, _ = model(vision, tactile, audio)

    # Losses
    action_loss = F.mse_loss(pred_actions, target_actions)
    value_loss = F.mse_loss(pred_values, target_values)
    total_loss = action_loss + 0.5 * value_loss

    # Backward pass
    optimizer.zero_grad()
    total_loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()

    return {
        'total_loss': total_loss.item(),
        'action_loss': action_loss.item(),
        'value_loss': value_loss.item()
    }


if __name__ == '__main__':
    print("=" * 60)
    print("Multi-modal Foundation Model for Humanoid Control")
    print("=" * 60)

    # Test forward pass
    print("\n[1/3] Testing forward pass...")
    actions, values, info = test_forward_pass()

    # Test training step
    print("\n[2/3] Testing training step...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = create_default_model().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

    batch_size = 8
    vision = torch.randn(batch_size, 768).to(device)
    tactile = torch.randn(batch_size, 128).to(device)
    audio = torch.randn(batch_size, 256).to(device)
    target_actions = torch.randn(batch_size, 56).to(device)
    target_values = torch.randn(batch_size, 1).to(device)

    losses = train_step(model, optimizer, vision, tactile, audio,
                      target_actions, target_values)

    print(f"  Action loss: {losses['action_loss']:.4f}")
    print(f"  Value loss: {losses['value_loss']:.4f}")
    print(f"  Total loss: {losses['total_loss']:.4f}")

    # Save model
    print("\n[3/3] Saving model checkpoint...")
    checkpoint = {
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'config': {
            'vision_dim': 768,
            'tactile_dim': 128,
            'audio_dim': 256,
            'hidden_dim': 1024,
            'action_dim': 56,
            'num_heads': 8,
        }
    }
    checkpoint_path = '/home/dietpi/.openclaw/workspace/research-system/experiments/20260314_015212/checkpoint.pth'
    torch.save(checkpoint, checkpoint_path)

    print(f"✓ Model saved to: {checkpoint_path}")

    print("\n" + "=" * 60)
    print("✓ Implementation complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Collect real-world data (vision + tactile + audio)")
    print("  2. Train on humanoid robot demonstrations")
    print("  3. Evaluate on contact-rich manipulation tasks")
    print("  4. Compare against vision-only baseline")
    print("\nNovel contribution:")
    print("  - Multi-modal fusion (vision + tactile + audio)")
    print("  - Learnable modality importance weighting")
    print("  - Cross-modal attention for information exchange")
